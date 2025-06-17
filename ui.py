from functools import cmp_to_key, partial
import gradio as gr
import qihan_index
import tantivy
import time
from datetime import datetime
from tantivy import SnippetGenerator

_MARKDOWN_CHARACTERS_TO_REMOVE = set("`*_{}[]<>()#+-.!|\n")

# Cleans up markdown characters from the search snippets.
def sanitize_markdown(text: str) -> str:
    return "".join(
        '' if character in _MARKDOWN_CHARACTERS_TO_REMOVE else character 
        for character in text
    )    

# Takes the query from the text box, runs the search, then outputs the results as
# a markdown string.
def run_search(query, version=0) -> str | None:
    if len(query) == 0:
        return None
    search_start_time = time.time()
    query = index.parse_query(query, ["title", "headers", "text", "misc", "url"], {"title":3, "headers":2, "text":1, "url":1, "misc":0.5})
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
        snippet = sanitize_markdown(snippet_generator.snippet_from_doc(doc).fragment())
        if len(snippet.strip()) == 0:
            snippet = "`No snippet available`"
        formatted_text = "# [" + sanitize_markdown(title) + "](" + doc["url"][0] + ")  \n" + snippet
        if output == '':
            output = formatted_text
        else:
            output += "\n\n" + formatted_text
        output += "\n\n[" + doc["url"][0] + "](" + doc["url"][0] + ")"
        output += "\n\n" + "Last Retrieved On: " + doc["retrieval_date"][0].strftime("%m/%d/%Y")
    results_parse_end_time = time.time()
    search_time_ms = (results_parse_end_time - search_start_time) * 1000
    output = "Search took " + str(search_time_ms) + " ms.\n\n\n\n" + output
    return output

# Loads some interesting crawler statistics to display 
def loadStats(filename="stats.txt"):
    total_stats = {"total_crawled":0, "total_indexed":0, "urls_seen":0, "url_error":0}
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
    domain_stats_list = []
    for item in domain_stats:
        domain_stats_list.append(domain_stats[item])
    return (total_stats, domain_stats_list)

def createStatsOverview():
    markdown = "# Overall Statistics"
    markdown += "\n\nTotal Urls Crawled: " + str(stats["total_stats"]["total_crawled"])
    markdown += "\n\nTotal Urls Indexed: " + str(stats["total_stats"]["total_indexed"])
    markdown += "\n\nTotal Urls Seen: " + str(stats["total_stats"]["urls_seen"])
    markdown += "\n\nBad Urls: " + str(stats["total_stats"]["url_error"])
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
    for i in range(len(stats["domain_stats"])):
        if empty_query or (query in stats["domain_stats"][i]["domain"]):
            markdown += domainToMarkdown(stats["domain_stats"][i])
            j += 1
            if j >= 100:
                break
    return markdown

# Comparer to sort domain statistics
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

# Reloads the index and crawl statistics
def reload():
    index.reload()
    (total_stats, domain_stats) = loadStats()
    domain_stats = sorted(domain_stats, key=cmp_to_key(compareDomainStats))
    stats["total_stats"] = total_stats
    stats["domain_stats"] = domain_stats
    return (createStatsOverview(), createDomainOverview())

schema = qihan_index.getSchema()
index = qihan_index.getIndex(schema=schema)
searcher = index.searcher()
stats = {"total_stats": {}, "domain_stats": []}

reload()

print("Launching UI")
with gr.Blocks() as search_ui:
    with gr.Accordion("Search", open=True):
        with gr.Row(equal_height=True):
            textbox = gr.Textbox(lines=1, show_label=False)
            button = gr.Button("Search", variant="primary")
        results = gr.Markdown("")
        textbox.submit(run_search, inputs=textbox, outputs=results)
        button.click(run_search, inputs=textbox, outputs=results)
    with gr.Accordion("Statistics", open=False):
        overall_stats_markdown = gr.Markdown(createStatsOverview())
        textbox = gr.Textbox(lines=1, show_label=False)
        domain_stats_markdown = gr.Markdown(createDomainOverview())
        textbox.change(createDomainOverview, inputs=textbox, outputs=domain_stats_markdown)
    search_ui.load(reload, outputs=(overall_stats_markdown, domain_stats_markdown))

search_ui.launch(share=True)
