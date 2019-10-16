from post_rec.tokenizers.tokenizerServer import TokenizerHTTPProxy

config_file="tokenizerService.json"
server=TokenizerHTTPProxy(config_file)

server.start()