from eve_analytics import EveAnalytics

logs_test_path = "/Users/zacharystocker/Documents/everepos/cloud-functions/cloud_functions_py/dev/download_logs/logs/2026-04-25"
save_path = "/Users/zacharystocker/Documents/test_docs/"

if __name__ == "__main__":
    # todo only takes 1 rn
    ea = EveAnalytics(logs_test_path)
    ea.parse_logs()
    ea.load_db()
    ea.generate_analytics("3878b93376dc875776e3208695dd9b19046383d8501fc5df25ab8954e924c1ea")
    # todo save analytics
    ea.save_analytics(save_path)
    #ea.generate_analytics()
    #ea.save_analytics(save_location)
    pass

