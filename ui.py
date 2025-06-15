from functools import cmp_to_key, partial
import gradio as gr
import qihan_index
import tantivy
import time
from tantivy import SnippetGenerator

_MARKDOWN_CHARACTERS_TO_REMOVE = set("`*_{}[]<>()#+-.!|\n")

def sanitize_markdown(text: str) -> str:
    return "".join(
        '' if character in _MARKDOWN_CHARACTERS_TO_REMOVE else character 
        for character in text
    )    

def get_field_boost(version):
    if version == 1:
        return {"title":3, "headers":2, "misc":0.5}
    if version == 2:
        return {"title":3, "headers":2, "text":1, "url":1, "misc":0.5}
    if version == 3:
        return {"title":2, "headers":2, "text":1, "url":1, "misc":0}
    return {}

def run_search(query, version=0) -> str | None:
    if len(query) == 0:
        return None
    search_start_time = time.time()
    query = index.parse_query(query, ["title", "headers", "text", "misc", "url"], get_field_boost(version))
    output = ""
    results = searcher.search(query, 10).hits
    search_end_time = time.time()
    
    snippet_generator = SnippetGenerator.create(
        searcher, query, schema, "text"
    )
    for i in range(min(len(results), 10)):
        (score, doc_address) = results[i]
        doc = searcher.doc(doc_address)
        title = doc["title"][0]
        snippet = snippet_generator.snippet_from_doc(doc)
        formatted_text = "# [" + sanitize_markdown(title) + "](" + doc["url"][0] + ")  \n" + sanitize_markdown(snippet.fragment())
        print(formatted_text)
        if output == '':
            output = formatted_text
        else:
            output = output + "\n\n" + formatted_text
    results_parse_end_time = time.time()
    search_time_ms = (results_parse_end_time - search_start_time) * 1000
    output = output + "\n\nSearch took " + str(search_time_ms) + " ms.\n\n\n\n"
    return output
    
def loadStats(filename="stats.txt"):
    total_stats = {"total_crawled":0, "total_indexed":0, "urls_seen":0, "mail_seen":0, "phone_seen":0}
    domain_stats = {}
    domain_keys = ["domain_crawled", "domain_indexed", "domain_seen"]
    with open(filename, 'r') as file:
        for line in file:
            line = line.strip(" \n")
            key_found = False
            for key in total_stats:
                if line.startswith(key + ": "):
                    total_stats[key] += int(line.removeprefix(key + ": "))
                    key_found = True
                    break
            if not key_found:
                for key in domain_keys:
                    if line.startswith(key + ":"):
                        line = line.removeprefix(key + ":")
                        i = line.rfind(' ')
                        if i >= 0:
                            domain = line[0:i]
                            count = line[i:]
                            if domain in domain_stats:
                                domain_stats[domain][key] = domain_stats[domain].get(key, 0) + int(count)
                            else:
                                domain_stats[domain] = {"domain": domain, key: int(count)}
    return (total_stats, domain_stats)

def createStatsOverview():
    markdown = "# Overall Statistics"
    markdown += "\n\nTotal Urls Crawled: " + str(total_stats["total_crawled"])
    markdown += "\n\nTotal Urls Indexed: " + str(total_stats["total_indexed"])
    markdown += "\n\nTotal Urls Seen: " + str(total_stats["urls_seen"])
    markdown += "\n\nEmail Links Seen: " + str(total_stats["mail_seen"])
    markdown += "\n\nPhone Links Seen: " + str(total_stats["phone_seen"])
    return markdown
    
def domainToMarkdown(domain):
    markdown = "\n## " + domain["domain"]
    if "domain_indexed" in domain:
        markdown += "\n\nurls indexed: " + str(domain["domain_indexed"])
    if "domain_crawled" in domain:
        markdown += "\n\nurls crawled: " + str(domain["domain_crawled"])
    if "domain_seen" in domain:
        markdown += "\n\nurls seen: " + str(domain["domain_seen"])
    return markdown

def createDomainOverview(query=""):
    markdown = "# Domain Statistics"
    j = 0
    empty_query = (query == "")
    for i in range(len(domain_stats_list)):
        if empty_query or (query in domain_stats_list[i]["domain"]):
            markdown += domainToMarkdown(domain_stats_list[i])
            j += 1
            if j >= 100:
                break
    return markdown
    
def compareDomainStats(domain1, domain2):
    if domain1.get("domain_indexed", 0) > domain2.get("domain_indexed", 0):
        return -1
    if domain1.get("domain_indexed", 0) < domain2.get("domain_indexed", 0):
        return 1
    if domain1.get("domain_crawled", 0) > domain2.get("domain_crawled", 0):
        return -1
    if domain1.get("domain_crawled", 0) < domain2.get("domain_crawled", 0):
        return 1
    if domain1.get("domain_seen", 0) > domain2.get("domain_seen", 0):
        return -1
    if domain1.get("domain_seen", 0) < domain2.get("domain_seen", 0):
        return 1
    if domain1["domain"] < domain2["domain"]:
        return -1
    if domain1["domain"] > domain2["domain"]:
        return 1
    return 0

print("Loading index")
schema = qihan_index.getSchema()
index = qihan_index.getIndex(schema=schema)
index.reload()
searcher = index.searcher()
(total_stats, domain_stats) = loadStats()
domain_stats_list = []
for item in domain_stats:
    domain_stats_list.append(domain_stats[item])
domain_stats_list = sorted(domain_stats_list, key=cmp_to_key(compareDomainStats))

print("Launching UI")
with gr.Blocks() as search_ui:
    with gr.Accordion("Search", open=True):
        with gr.Row(equal_height=True):
            textbox = gr.Textbox(lines=1, show_label=False)
            button = gr.Button("Search", variant="primary")
            button1 = gr.Button("Search1", variant="primary")
            button2 = gr.Button("Search2", variant="primary")
            button3 = gr.Button("Search3", variant="primary")
        results = gr.Markdown("")
        button.click(run_search, inputs=textbox, outputs=results)
        button1.click(partial(run_search, version=1), inputs=textbox, outputs=results)
        button2.click(partial(run_search, version=2), inputs=textbox, outputs=results)
        button3.click(partial(run_search, version=3), inputs=textbox, outputs=results)
    with gr.Accordion("Statistics", open=False):
        gr.Markdown(createStatsOverview())
        textbox = gr.Textbox(lines=1, show_label=False)
        domain_stats_markdown = gr.Markdown(createDomainOverview())
        textbox.change(createDomainOverview, inputs=textbox, outputs=domain_stats_markdown)

search_ui.launch(share=False)
