from post_rec.retrievers.relation_searcher import KnowAlphaHTTPProxy

config_file="knowAlphaService.json"
server=KnowAlphaHTTPProxy(config_file)

server.start()