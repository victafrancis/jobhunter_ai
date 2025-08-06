import streamlit as st
import streamlit.components.v1 as components

def quill_editor(default_value="", height=400, key="quill"):
    html_code = f"""
    <div id="{key}" style="height:{height}px;">
      <link href="https://cdn.quilljs.com/1.3.6/quill.snow.css" rel="stylesheet">
      <script src="https://cdn.quilljs.com/1.3.6/quill.min.js"></script>

      <style>
        .ql-container {{
          background-color: white;
          color: black;
          font-family: 'Georgia', serif;
          font-size: 16px;
        }}
        .ql-editor {{
          min-height: {height - 50}px;
        }}
      </style>

      <div id="editor-container-{key}" style="height:100%;"></div>

      <script>
        const container = document.getElementById("editor-container-{key}");
        container.innerHTML = `{default_value}`;
        const quill = new Quill(container, {{
          theme: 'snow'
        }});

        const form = window.parent.document.querySelector("form");
        form.onsubmit = () => {{
          const hiddenInput = window.parent.document.getElementById("quill-input-{key}");
          hiddenInput.value = quill.root.innerHTML;
        }};
      </script>

      <input type="hidden" name="quill-input-{key}" id="quill-input-{key}">
    </div>
    """

    # Display the editor
    components.html(html_code, height=height + 50)

    # Get submitted value
    submitted_value = st.session_state.get(f"quill-input-{key}", default_value)
    return submitted_value
