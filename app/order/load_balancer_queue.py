import zmq


def main():

    try:
        context = zmq.Context(1)
        # Socket facing clients
        gateway = context.socket(zmq.XREP)
        gateway.bind("tcp://*:5559")
        # Socket facing services
        backend = context.socket(zmq.XREQ)
        backend.bind("tcp://*:6666")

        zmq.device(zmq.QUEUE, gateway, backend)
    except Exception as e:
        print(e)
        print("bringing down zmq device")
    finally:
        pass
        gateway.close()
        backend.close()
        context.term()


if __name__ == "__main__":
    main()
