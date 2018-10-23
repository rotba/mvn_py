from sfl_diagnoser.Diagnoser.diagnoserUtils import readPlanningFile, write_planning_file, write_merged_matrix
# from sfl_diagnoser.Diagnoser.diagnoserUtils import readPlanningFile, write_planning_file, write_merged_matrix
# from sfl_diagnoser.Diagnoser.Diagnosis_Results import Diagnosis_Results


def merge_same_components(self):
    components_vector = {}
    for test in self.TestsComponents:
        for component in test:
            components_vector.setdefault(component, []).append(test)
    similiar_componets = {}
    for component in components_vector:
        similiar_componets.setdefault(str(sorted(components_vector[component])), []).append(component)


def check_influence():
    base = readPlanningFile(r"c:\temp\base_matrix.txt")
    base.diagnose()
    base_results = Diagnosis_Results(base.diagnoses, base.initial_tests, base.error)
    added = readPlanningFile(r"c:\temp\added_matrix.txt")
    added.diagnose()
    added_results = Diagnosis_Results(added.diagnoses, added.initial_tests, added.error)
    pass

def get_xref_diagnoses(instance, seperator="$"):
    def xref_comp_to_function(xref_comp):
        return xref_comp.split(seperator)[1]
    instance.diagnose()
    diagnoses = map(lambda diagnosis: map(xref_comp_to_function, diagnosis), instance.diagnoses)
    for diagnosis in diagnoses:
        diagnosis.diagnosis = list(set(diagnosis))
    return diagnoses

def abstraction():
    write_planning_file(r"c:\temp\yemp_matrix.txt", ["a"], [["T1", ["a", "b", "d"], 1],
                                                            ["T2", ["b"], 0],
                                                            ["T3", ["a", "b", "c"], 1],
                                                            ["T4", ["a", "b", "c"], 0]])
    instance = readPlanningFile(r"c:\temp\yemp_matrix.txt")
    write_planning_file(r"c:\temp\yemp_matrix.txt", ["a"], [["T1", ["a", "b", "d"], 1],
                                                            ["T2", ["b"], 0],
                                                            ["T3", ["a", "b"], 1],
                                                            ["T4", ["a", "b"], 0]])
    instance = readPlanningFile(r"c:\temp\yemp_matrix.txt")
    write_planning_file(r"c:\temp\yemp_matrix.txt", ["a"], [["T1", ["a", "b"], 1],
                                                            ["T2", ["b"], 0],
                                                            ["T3", ["a", "b"], 1],
                                                            ["T4", ["a", "b"], 0]])
    instance = readPlanningFile(r"c:\temp\yemp_matrix.txt")
    print "a"


if __name__ == "__main__":
    from sfl_diagnoser.Diagnoser.diagnoserUtils import readPlanningFile
    from sfl_diagnoser.Diagnoser.Diagnosis_Results import Diagnosis_Results
    import sfl_diagnoser.Diagnoser.ExperimentInstance

    inst = readPlanningFile(r"C:\Users\User\Downloads\inputMatrix6_amir.txt")
    inst.diagnose()
    results = Diagnosis_Results(inst.diagnoses, inst.initial_tests, inst.error)
    results.get_metrics_names()
    results.get_metrics_values()
    print results
    exit()
    ei = sfl_diagnoser.Diagnoser.ExperimentInstance.addTests(inst, inst.hp_next())

    # check_influence()
    # exit()
    base = readPlanningFile(r"C:\Users\User\Downloads\MatrixFile4.txt")
    from sfl_diagnoser.Planner.HP_Random import main_HP
    main_HP(base)


    abstraction()
    write_planning_file(r"c:\temp\yemp_matrix.txt", ["a"], [["T1", ["a", "c"], 1],
                                                            ["T2", ["b"], 0],
                                                            ["T3", ["a", "b"], 1],
                                                            ["T4", ["a", "b", "c"], 0]])
    write_planning_file(r"c:\temp\yemp_matrix2.txt", ["a"], [["T1", ["a", "b"], 1],
                                                            ["T2", ["b"], 0],
                                                            ["T3", ["a", "b"], 1],
                                                            ["T4", ["a", "b"], 0]])
    instance = readPlanningFile(r"c:\temp\yemp_matrix.txt")
    instance = readPlanningFile(r"c:\temp\yemp_matrix2.txt")
    instance = readPlanningFile(r"C:\Users\User\Dropbox\softwareMbd (1)\Amir_AAAI18\vulnerability example\code_blocks_matrix.txt")
    instance.get_named_diagnoses()
    named =get_xref_diagnoses(instance.get_named_diagnoses(),"#")
    # instance = readPlanningFile(r"c:\temp\merged_matrix.txt")
    function_instance = readPlanningFile(r"C:\vulnerabilities\ImageMagick_exploited\CVE-2016-8866\fuzzing\function_matrix.txt")
    xref_instance = readPlanningFile(r"C:\vulnerabilities\ImageMagick_exploited\CVE-2016-8866\fuzzing\xref_matrix.txt")
    # write_merged_matrix(function_instance, r"c:\temp\function_merged_matrix.txt")
    write_merged_matrix(xref_instance, r"c:\temp\xref_merged_matrix.txt")
    # function__merged_instance = readPlanningFile(r"c:\temp\function_merged_matrix.txt")
    xref__merged_instance = readPlanningFile(r"c:\temp\xref_merged_matrix.txt")
    # instance = readPlanningFile(r'C:\\vulnerabilities\\ImageMagick_exploited\\CVE-2017-5510\\fuzzing\\function_matrix.txt')
    # instance = readPlanningFile(r'C:\\vulnerabilities\\ImageMagick_exploited\\CVE-2017-5510\\fuzzing\\dll_matrix.txt')
    # instance.diagnose()
    # function_instance.diagnose()
    ds = xref_instance.initials_to_DS()
    ds2 = ds.remove_duplicate_tests()
    ds2.save_to_matrix_file(r"c:\temp\5506.txt")
    new_instance = readPlanningFile(r"c:\temp\5506.txt")
    # new_instance.diagnose()
    # xref_instance.diagnose()
    # function__merged_instance.diagnose()
    # xref__merged_instance.diagnose()
    instance.get_optionals_actions()
    named = instance.get_components_probabilities_by_name()
    functions = map(lambda x: (x[0].split("^")[0].split("$")[1],x[1]), filter(lambda x: '$'in x[0], named))
    function_probs = {}
    for name, probability in functions:
        function_probs[name] = function_probs.get(name, 0) + probability
    s = sorted(function_probs.items(), key=lambda x: x[1], reverse=True)
    print instance.calc_precision_recall()
    print s

    exit()


    instance = readPlanningFile(r"C:\vulnerabilities\ImageMagick_exploited\CVE-2017-5510\fuzzing\XREF_matrix.txt")
    # instance = readPlanningFile(r"C:\vulnerabilities\ImageMagick_exploited\CVE-2017-5510\fuzzing\function_diagnosis_matrix.txt")
    precision, recall = instance.calc_precision_recall()
    print instance.count_different_cases() , precision, recall

    dll_diagnosis("function_diagnosis_matrix.txt", "function_diagnosis_result.csv")
    pass