import gradio as gr
import qihan_index
import tantivy
from tantivy import SnippetGenerator
from bs4 import BeautifulSoup

print("Loading index")
schema = qihan_index.getSchema()
index = qihan_index.getIndex(schema=schema)
index.reload()
searcher = index.searcher()

def run_search(query) -> str | None:
    if len(query) == 0:
        return None
    query = index.parse_query(query, ["title", "text"])
    output = ""
    results = searcher.search(query, 3).hits
    
    snippet_generator = SnippetGenerator.create(
        searcher, query, schema, "text"
    )
    for i in range(min(len(results), 10)):
        (score, doc_address) = results[i]
        doc = searcher.doc(doc_address)
        title = doc["title"][0]
        snippet = snippet_generator.snippet_from_doc(doc)
        formatted_text = "# [" + title + "](" + doc["url"][0] + ")  \n" + snippet.fragment()
        print(formatted_text)
        if output == '':
            output = formatted_text
        else:
            output = output + "\n\n" + formatted_text
    return output

print("Launching UI")
with gr.Blocks() as search_ui:
    with gr.Row(equal_height=True):
        textbox = gr.Textbox(lines=1, show_label=False)
        button = gr.Button("Search", variant="primary")
    results = gr.Markdown("")
    button.click(run_search, inputs=textbox, outputs=results)

search_ui.launch(share=False)
