from urllib.parse import urlparse

# Matches the url to one of the domains in the set of domains
# Matches the longest subdomain first.
# If the domain isn't in the set, returns the second level domain of the url.
def matchDomain(domains, url):
	domain = urlparse(url).netloc
	# Majority of the time, the domain should be an exact match
	if domain in domains:
		return domain
	# Check for subdomain matches starting with the longest.
	split_domain = domain.split('.')
	for i in range(1, len(split_domain)):
		d = '.'.join(split_domain[i:])
		if d in domains:
			return d
	if len(split_domain) >= 2:
		# If it's not found, just return the second level domain.
		return '.'.join(split_domain[-2:])
	return ''