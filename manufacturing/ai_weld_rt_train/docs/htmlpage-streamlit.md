# HTML page of streamlit
## code block

```
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>My Website with Streamlit</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f4f4f9;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        /* Styling the iframe wrapper for responsiveness */
        .iframe-container {
            position: relative;
            width: 100%;
            height: 800px; /* Adjust height based on your app's content */
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
            border-radius: 8px;
            overflow: hidden;
        }
        iframe {
            width: 100%;
            height: 100%;
            border: none;
        }
    </style>
</head>
<body>

    <div class="container">
        <h2>Data Dashboard</h2>
        <p>Below is the interactive Streamlit application embedded directly into this page.</p>
        
        <div class="iframe-container">
            <iframe 
                src="https://your-streamlit-app-url.streamlit.app/?embed=true"
                allow="geolocation; microphone; camera"
                sandbox="allow-forms allow-modals allow-popups allow-popups-to-escape-sandbox allow-same-origin allow-scripts align-top">
            </h1>
        </div>
        </div>

</body>
</html>