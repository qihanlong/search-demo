import gradio as gr

def run_search(query):
    print(query)

with gr.Blocks() as search_ui:
	with gr.Row(equal_height=True):
		textbox = gr.Textbox(lines=1, show_label=False)
		button = gr.Button("Search", variant="primary")
	button.click(run_search, inputs=textbox)
	
search_ui.launch(share=True)
