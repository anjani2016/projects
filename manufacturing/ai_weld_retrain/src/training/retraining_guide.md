# Weld Joint Radiography Model Retraining & Optimization Guide

This guide details the mathematical foundations, dataset splitting strategies, and hyperparameter optimization (HPO) techniques implemented in this NDT quality control retraining pipeline.

---

## 1. Multi-Component Loss Function Optimization

Industrial object detection requires optimizing bounding box locations, category labels, and edge boundaries simultaneously. Ultralytics YOLOv11 and Baidu RT-DETR model this using a multi-component loss function:

$$\text{Total Loss} = \lambda_{\text{box}} \mathcal{L}_{\text{box}} + \lambda_{\text{cls}} \mathcal{L}_{\text{cls}} + \lambda_{\text{dfl}} \mathcal{L}_{\text{dfl}}$$

### A. Bounding Box Localization Loss ($\mathcal{L}_{\text{box}}$)
Standard Mean Squared Error (MSE) on coordinates is sensitive to object scale and aspect ratios. To solve this, we use **Complete Intersection over Union (CIoU) Loss**:

$$\mathcal{L}_{\text{box}} = 1 - \text{IoU} + \frac{\rho^2(b, b^{gt})}{c^2} + \alpha v$$

* **$\text{IoU}$**: Area of intersection divided by area of union.
* **$\rho^2(b, b^{gt})$**: Euclidean distance between the center points of the predicted box ($b$) and ground-truth box ($b^{gt}$).
* **$c$**: Diagonal length of the smallest enclosing bounding box that covers both boxes.
* **$\alpha v$**: Aspect ratio consistency term:
  $$v = \frac{4}{\pi^2} \left( \arctan \frac{w^{gt}}{h^{gt}} - \arctan \frac{w}{h} \right)^2$$
  $$\alpha = \frac{v}{(1 - \text{IoU}) + v}$$

**Tuning Rule:** If the model detects defects but fails to tightly bound them (high $\mathcal{L}_{\text{box}}$ on validation), increase the `box` gain parameter (default `7.5`).

---

### B. Classification Loss ($\mathcal{L}_{\text{cls}}$)
To handle severe class imbalances (e.g., millions of background pixels vs. a few dozen pixels representing a micro-crack), we replace standard Binary Cross Entropy (BCE) with **Focal Loss**:

$$\mathcal{L}_{\text{cls}} = -\alpha_t (1 - p_t)^\gamma \log(p_t)$$

* **$p_t$**: Model's estimated probability for the correct ground truth class.
* **$\gamma$ (gamma)**: Focusing parameter (default `0.0`, which reduces to standard BCE). Setting $\gamma > 0$ (e.g. `2.0`) down-weights the loss contribution of well-classified "easy" examples (confidence $p_t \approx 1.0$), forcing gradients to be dominated by hard, misclassified "rare" examples.
* **$\alpha_t$**: Balancing parameter to weigh positive vs. negative examples.

**Tuning Rule:** If the model misses critical defects (like micro-cracks) due to background noise or class rarity, set `fl_gamma = 2.0` (activating Focal Loss) and increase the classification gain `cls` (default `0.5`).

---

### C. Distribution Focal Loss ($\mathcal{L}_{\text{dfl}}$)
Modern detectors represent bounding box coordinates not as single numbers, but as discrete probability distributions over a set of bin values. This models the uncertainty of boundary edges, which is highly beneficial for blurry, low-contrast NDT radiography films:

$$\mathcal{L}_{\text{dfl}}(S_i, S_{i+1}) = -((y_{i+1} - y)\log(S_i) + (y - y_i)\log(S_{i+1}))$$

* **$y$**: The actual continuous edge coordinate.
* **$y_i, y_{i+1}$**: Nearest discrete bin boundaries.
* **$S_i, S_{i+1}$**: Softmax outputs (probabilities) for bins $i$ and $i+1$.

**Tuning Rule:** If the defect edges are highly graduated or noisy, increase the `dfl` gain parameter (default `1.5`) to penalize boundary uncertainty.

---

## 2. Stratified 5-Fold Cross-Validation

Object detection annotations are multi-label (an image can contain multiple defect bounding boxes). Simple random splitting can lead to **data leakage** or leave rare classes entirely out of either the validation or test splits.

### Multi-Label Stratification Heuristic
To solve this without external dependencies, `stratified_splitter.py` implements a **Rarity-Based Stratification Heuristic**:
1. Scan all annotations to calculate the global frequency of each class.
2. Rank classes from rarest to most common.
3. For each image, scan its labels and assign it to the stratum of the **rarest class it contains**.
4. Images with no annotations are assigned to a special "background" stratum (`-1`).
5. Use `sklearn.model_selection.StratifiedKFold` on this single-class mapping. This guarantees that scarce classes (like `crack`) are split evenly across:
   * **Holdout Test Set (15%)**: Final unbiased evaluation.
   * **5 Folds (85% Train/Val Pool)**: For training and cross-validation performance averaging.

---

## 3. Automated HPO & Median Pruning

Manually tuning parameters like learning rates and regularizers is computationally expensive. We wrap our pipeline in **Optuna** to automate this.

```
Trial 1 ── [Epoch 1] ── [Epoch 2] ── [Epoch 3] (Validation score: 0.12)
Trial 2 ── [Epoch 1] ── [Epoch 2] (Validation score: 0.02) ──> PRUNED! (Below median)
```

### Optuna Median Pruner Mechanics
1. **Search Space:**
   * `lr0` (Initial Learning Rate): Log-uniform [$10^{-5}$, $10^{-2}$].
   * `weight_decay` (L2 Regularization): Uniform [$10^{-4}$, $10^{-2}$].
   * `batch` (Categorical): `[16, 32, 64]`.
   * `box` (Localization gain): Uniform `[2.0, 10.0]`.
2. **Median Pruning Policy:**
   * At the end of each epoch, the callback reports the validation `mAP@0.5:0.95` to Optuna.
   * Optuna compares this score to the historical median score of all previous trials at that exact same epoch step.
   * If the current trial's score is below the median of completed trials, Optuna raises `TrialPruned`, which halts training and immediately launches the next trial configuration.
   * This saves up to 70% of total HPO computing time by aborting poor configurations early.

---

## 4. How to Run the Pipeline

### Step 1: Split the Gazprom Dataset
Combine the dataset, extract the holdout test set, and build the 5 folds. We will use a subset size of `500` for rapid development validation:

```bash
PYTHONPATH=. python3 src/training/stratified_splitter.py \
    --dataset_dir /Users/anjanid/projects/manufacturing/ai_weld_rt_train/data/gazpromneft_kaggle \
    --output_dir data/split_folds \
    --subset_size 500
```

### Step 2: Run a Trial Training Run
Train a single fold (e.g. Fold 1) with specific custom parameters and log it to MLflow:

```bash
PYTHONPATH=. python3 src/training/train_pipeline.py \
    --modelweights weights/rtdetr-l.pt \
    --data data/split_folds/data_fold_1.yaml \
    --epochs 5 \
    --batch 16 \
    --box 9.0 \
    --cls 1.0 \
    --fl_gamma 2.0 \
    --lr0 0.001
```

### Step 3: Run the Hyperparameter Tuning Loop
Run 5 trials of HPO to search for the best configuration using Median Pruning:

```bash
PYTHONPATH=. python3 src/training/hpo_pipeline.py \
    --data_dir data/split_folds \
    --modelweights weights/rtdetr-l.pt \
    --n_trials 5 \
    --epochs_per_trial 5 \
    --patience 3
```

### Step 4: Open the MLflow Dashboard
View live training curves, trial comparisons, and parameters:

```bash
mlflow ui
```
Open [http://localhost:5000](http://localhost:5000) in your web browser.
