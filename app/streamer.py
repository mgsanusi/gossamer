import zmq

def main():
    try:
        context = zmq.Context(1)
        # Socket facing clients
        frontend = context.socket(zmq.PULL)
        frontend.bind("tcp://*:5559")
        
        # Socket facing services
        backend = context.socket(zmq.PUSH)
        backend.bind("tcp://*:5560")

        zmq.device(zmq.STREAMER, frontend, backend)
    except Exception as e:
        print(e)
        print("Bringing down zmq device")
    finally:
        pass
        frontend.close()
        backend.close()
        context.term()

if __name__ == "__main__":
    main()
