from post_rec.answer_generations.AnswerNetServices import AnswerAlphaHTTPProxy

config_file="answerAlphaService.json"
server=AnswerAlphaHTTPProxy(config_file)

server.start()

