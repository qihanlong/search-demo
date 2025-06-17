# Overview

For a project of this scale, I like to use python for convenience. So ideally, I'm looking for libraries that's compatible with python. The network latency should dominate for crawling, but the index will need to be offloaded to a faster language for searching.

## Indexing

I only had two choices for the index, either Tantivy or Vespa. Since the crawler will need to be compatible with the chosen index, I decided to start here. I've got the following take aways after reading the documentation for the two.

### Vespa

- Features scalable containers for cloud deployment.
- Each container can be individually scaled for performance.
- Features embedding searches in addition to tokenized searching.
- Primarily interacted through the commandline.

### Tantivy

- Built on Rust.
- Provided [benchmarks](https://tantivy-search.github.io/bench/) are all well below the 50ms target.
- Has a python library in tantivy-py, but documentation for python is limited.

Overall, both indices looks like they can work. However, Vespa's features looks like its more useful for a full scaled production search engine, but introduces more complexities for a small scale project. Tantivy seems much easier to develop for, and would be more appropriate for a test project. The python library is risky due to its limited API, but I preferred the convenience. Finally, I've ran into issues trying to install and set up Vespa, so I decided to go ahead with Tantivy.

## Crawler

Crawling is as simple as downloading a website's contents and following the urls in the links. So, I'm looking for a library that offers features of a well behaved web crawler that integrates well with the indexing engine and project requirements. Scrapy offered a lot of useful features, but the ones that stood out to me are:

- Built in domain restrictions
- Built in deduping features
- Scheduling and throttling
- Follows Robots.txt
- Automatic url extraction
- html querying utilities

My implementation followed Scrapy's general guidelines, with the home page of the domain as the starting urls. On top of Scrapy, I wrote the code to handle the url selection, per domain max crawl restrictions, and integration with Tantivy. Since we're looking for code documentation, I used Scrapy's priority queue to prioritize urls that include substrings related to code such as `api`, `doc`, and `wiki`. I've also deprioritized some substrings related to infinite spaces that we're not as interested in like `forum` or `community` to avoid wasting bandwidth. Urls ending in `.html` were bumped up in priority because we're looking for html content for processing, though some sites might return documentation with a different extension in the url. Finally, `.pdf`, `.zip`, and `.gz` were dropped because we can't process them.

Handling the per domain cap was trickier due to Scrapy's architecture. If I set the capped a domain at indexing time, I couldn't easily clean out the urls that were already queued, causing a lot of urls that would be crawled only to be dropped. Checking for the cap in the spider before sending the next request to the scheduler would cause the url to be deduped, but still counted towards the cap. So, I extended the scheduler to check for the domain cap right before it is queued. This would mean that the number of indexed pages would be slightly lower since some pages are dropped after the crawler sees the contents, but in practice it would be quite close. If the 10,000 domain cap had to be strictly followed, I would implement the check at both the indexing time and the scheduling time, with the scheduling cap being slightly higher.

When integrating with Tantivy, I used Scrapy's built in xpath html selectors to choose the content that would be indexed. I didn't do too much tweaking on this, but I used it to select the page title, headers, `<p>`, `<div>`, and `<span>` text. I hacked a check to make sure that the text has a minimum size (~4 characters) to avoid filling the index with content that can't be searched.

### Domain Restrictions

Scrapy provides a domain restriction feature in its `allowed_domains` field. This was pretty helpful, but I found a few of the sites redirecting the relevant content to other domains. For the ones I've found, I manually added the external domains to the domain restrictions field, but I didn't thoroughly check all of them. So plenty of content was probably missed.

### Http proxy

Scrapy provides built in middleware for handling http proxies if necessary. The exact details would depend on the exact purpose of the proxy. Usually, the http proxy uses I've seen are for accessing region locked content, minimizing reliance on public networks, or for cloaking.

### Other Crawlers Considered:

I've found a few other crawling libraries that I didn't go with.

- [Mechanical Soup](https://github.com/MechanicalSoup/MechanicalSoup): Simple browser emulator that doesn't support javascript. It can be used to follow links and extract content, but doesn't have many additional features. If I used this, I'd have to build out the scheduler, robots.txt, and dupe removal myself.
- [Selenium](https://github.com/SeleniumHQ/selenium): A more robust browser simulator than MechanicalSoup, mostly in the form of javascript rendering and browser simulation. However, it doesn't offer any additional crawling features.
- [Crawl4ai](https://github.com/unclecode/crawl4ai) and [Crawlee](https://github.com/apify/crawlee): Both immediately advertised their ability to avoid bot detection. This is the opposite of what I want from a search engine bot, so I decided to come back to these later if I didn't find a more appropriate library.

## UI

For the UI, I used Gradio just out of simplicity and familiarity. This wouldn't be my choice for a production search engine. The search outputs are displayed in a markdown block, which I find to often format the snippets in unexpected ways. I've added a markdown cleaner to remove the markdown symbols from the snippets, but it still gets occasionally lets things slip through.

## Performance

My initial index and search implementation had latency issues, sometimes hitting 200ms. The first time a query is executed on my home computer, the latency would spike up to 160ms. Then the latency would drop down to around 15ms for repeated attempts, probably due to caching. On the GCP VM for the demo, the latency would consistently hit higher regardless of whether its the first or repeat of a query. I did two things to reduce the latency, it now runs under 10ms on demo machine.

- Increased the cloud VM's RAM to 16GB from 4GB.
- Reduced the index size.
	- Removed the html body from the index since that was just for testing and not actually used for searching.
	- No longer index any text that's less than 2 characters for `<p>` tags and 4 characters for `<div>` and `<span>` tags.

Tantivy's python library only had limited controls for manipulating the index. For example, the Rust version had multithreading controls that I can't access through python. In addition, I noticed that Vespa provided a timeout in its API, which would be helpful for setting a hard limit. I didn't see anything similar in Tantivy.

I've considered dropping the `<div>` and `<span>` tags from the index, but they didn't quite have a negative impact on the index after suppressing short text lengths. Some websites may put text directly in those two tags, but I haven't encountered one in the domains that I've checked.

Overall, I think reducing the index size had the biggest impact on latency reduction. In my first version, a lot of entries were indexed with no real searchable content, likely from divs that just contain other elements. As of my last test, the index consisted of 160,000 documents and search took around 4ms. There will be more latency as the index grows, but it shouldn't go over 50ms.

## Search Relevancy

I left the search optimizations fairly simple since I don't expect too much SEO abuse in the domain restrictions. Since the index composed of the text in the page title, headers, `<p>`, `<div>`, and `<span>` tags, I weighted the search query roughly in that order. The title had the highest weight and the `<div>` and `<span>` tags had the same minimal weight.

I've tried multiple different boost weight distributions as well as adding some hidden weighted terms to the query (i.e. `api` or `documentation`), but I didn't see much of a difference. This could have been contributed by the smaller crawl runs I used for testing. Downloading significant number of documents from a domain could take hours if I didn't want to risk getting banned. So iterating on the index was difficult.

Overall, I think the quality of the search results still leaves much to be desired and is definitely a shortcoming of this search engine.

## Other Notes

The crawler doesn't interact well with restarting. Once restarted, it will lose track of the queue and dupes resulting in recrawling much of the same sites. This isn't an issue if freshness is needed, but restarts could prevent the crawler from finding new pages due to excessive recrawls. Restarts also clears the internal counters on the crawl caps. So a new crawl can allow the index to go over the 10,000 urls per domain cap. A production ready crawler should not have this limitation.

There can be race conditions in the crawler. I'm unfamiliar with Twisted Reactor (Scrapy's event scheduler) nor did I have the time to dig into Scrapy's implementation. From what I can tell, the code I implemented should be single threaded, but the documentation only implied that. I didn't notice any race conditions appearing either, but this is something I'd investigate in greater deal for a larger scale project. 



