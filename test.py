from chase.session import ChaseSession

cs = ChaseSession(persistant_session=True, docker=False)
cs.login('username', 'password', 4374)

