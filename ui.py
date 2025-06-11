import gradio as gr
import qihan_index
import tantivy

def run_search(query):
    query = index.parse_query(query, ["title", "body"])
    (best_score, best_doc_address) = searcher.search(query, 3).hits[0]
    best_doc = searcher.doc(best_doc_address)
    print(best_doc["title"])

print("Loading index")
index = qihan_index.getIndex()
index.reload()
searcher = index.searcher()

print("Launching UI")
with gr.Blocks() as search_ui:
	with gr.Row(equal_height=True):
		textbox = gr.Textbox(lines=1, show_label=False)
		button = gr.Button("Search", variant="primary")
	button.click(run_search, inputs=textbox)

search_ui.launch(share=False)
