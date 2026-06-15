import content

def test_content_functions():
    assert isinstance(content.get_intro_text(), str)
    assert len(content.get_intro_text()) > 0
    
    assert isinstance(content.get_definitions(), str)
    assert len(content.get_definitions()) > 0
    
    assert isinstance(content.get_bridge_content(), str)
    assert len(content.get_bridge_content()) > 0
    
    assert isinstance(content.get_real_world_examples(), str)
    assert len(content.get_real_world_examples()) > 0
    
    assert isinstance(content.get_sidebar_info(), str)
    assert len(content.get_sidebar_info()) > 0
