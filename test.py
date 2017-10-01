from tests.test_downloader import MFTests


def main():
    ts = MFTests()
    ts.test_log_handler()
    ts.test_server()

main()