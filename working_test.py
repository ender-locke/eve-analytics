from eve_analytics import EveAnalytics

logs_test_path = "/Users/zacharystocker/Documents/everepos/cloud-functions/cloud_functions_py/dev/download_logs/logs/2026-04-25"
ea = EveAnalytics(logs_test_path)

if __name__ == "__main__":
    ea.parse_logs()
    pass

