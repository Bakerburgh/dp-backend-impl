# import connexion.app


def dev_repl_post(body):
    if body is None:
        return 'Bad Input', 400
    if type(body) == bytes:
        body = body.decode()

    print('REPL: ' + body)
    try:
        result = str(eval(body))
    except Exception as e:
        print(e)
        return str(e), 400
    print(result)
    return result