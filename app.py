import gradio as gr
from bot import Me
import os

me = Me()

def respond(message, history):
    history = me.chat(message, history)
    return history, history, ""  # Chatbot, state, clear textbox

with gr.Blocks(title="Alaa Allam - CV Assistant") as demo:
    gr.Markdown("""
    # 🤖 Alaa Allam's CV Assistant  
    Ask me anything about my resume, experience, or professional background.
    """)

    chatbot = gr.Chatbot(label="Chat with Alaa", bubble_full_width=False)
    state = gr.State([])

    with gr.Row():
        msg = gr.Textbox(placeholder="Ask me about Alaa's experience...", scale=4)
        submit = gr.Button("Send", variant="primary")

    submit.click(respond, [msg, state], [chatbot, state, msg])
    msg.submit(respond, [msg, state], [chatbot, state, msg])

# Launch with public share URL
port = int(os.environ.get("PORT", 7860))
demo.launch(server_name="0.0.0.0", server_port=port)