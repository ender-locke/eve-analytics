from eve_analytics import EveAnalytics

logs_test_path = "/Users/zacharystocker/Documents/everepos/cloud-functions/cloud_functions_py/dev/download_logs/logs/2026-04-25"


if __name__ == "__main__":
    # todo only takes 1 rn
    ea = EveAnalytics(logs_test_path)
    ea.parse_logs()
    ea.load_db()
    # todo load the sde data
    #  groups.yaml = invgroups table
    #  categories.yaml = invcategoires table
    #  types.yaml = invtypes table
    #  typedogma.yaml appears to be dmgtypesattribs <- idk why i need this
    #ea.generate_analytics()
    #ea.save_analytics(save_location)
    pass

