# -*- coding: utf-8 -*-

import os
import fitz
import gradio as gr
from PIL import Image

from main import plan, execute, reword_response

CSS = """
.gr-label {
    height: 800px;  /* Limiting height */
    overflow-y: auto;   /* Adding vertical scrollbar */
}
"""

def chatfunction(user_input, chat_history):
    categories, reformatted_queries = plan(user_input)
    agent_responses, jinie_output = execute(user_input, reformatted_queries, categories)
    final_answer = reword_response(user_input, agent_responses, jinie_output)
    chatbot_output = f"<b>Answer:</b> {final_answer}"
    chat_history.append((user_input, chatbot_output))
    return None, chat_history

def clearchat():
    return None, None, None, None, None, None, None, None, None

with gr.Blocks(css=CSS) as api_demo_ui:
    gr.Markdown("Ishaan Chatbot | CWD: {}".format(os.getcwd()))
    with gr.TabItem("OpenAI RAG"):
        with gr.Row():
            with gr.Column():
                with gr.Row():
                    user_input = gr.Textbox(show_label=False, scale=2)
                    clear_button = gr.Button("🗑️  Clear", scale=1)
                chatbot = gr.Chatbot(height=600)

    user_input.submit(fn=chatfunction,
                      inputs=[user_input, chatbot],
                      outputs=[user_input, chatbot])
    clear_button.click(fn=clearchat, inputs=[],
                       outputs=[user_input, chatbot])

api_demo_ui.launch(server_name="0.0.0.0")
