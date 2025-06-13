import gradio as gr
import qihan_index
import tantivy
from bs4 import BeautifulSoup

def run_search(query) -> str | None:
    if len(query) == 0:
        return None
    query = index.parse_query(query, ["title", "body"])
    output = ""
    results = searcher.search(query, 3).hits
    for i in range(min(len(results), 10)):
        (score, doc_address) = results[i]
        doc = searcher.doc(doc_address)
        print(doc["title"][0])
        title = BeautifulSoup(doc["title"][0], "lxml").text
        formatted_text = "# " + title
        if output == '':
            output = formatted_text
        else:
            output = output + "\n\n" + formatted_text
    return output

print("Loading index")
index = qihan_index.getIndex()
index.reload()
searcher = index.searcher()

print("Launching UI")
with gr.Blocks() as search_ui:
    with gr.Row(equal_height=True):
        textbox = gr.Textbox(lines=1, show_label=False)
        button = gr.Button("Search", variant="primary")
    results = gr.Markdown("")
    button.click(run_search, inputs=textbox, outputs=results)

search_ui.launch(share=False)
