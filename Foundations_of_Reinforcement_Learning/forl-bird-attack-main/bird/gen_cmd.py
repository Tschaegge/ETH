if __name__=='__main__':

    scaling_method = "identity" # "identity", "negative", "exponential decay", "sigmoid complement", "negative tanh", "negative cubic", "hash"
    save_trigger = True
    dir_path = "identity_st1"
    use_seeds = False
    strong_targeted = True

    for i in range(20):
        save_trigger_str = "--save_trigger" if save_trigger else ""
        seed_str = "--seed " + str(i) if use_seeds else ""
        strong_targeted_str = "--strong_targeted" if strong_targeted else ""
        cmd = f"python restore.py {save_trigger_str} --dir_path {dir_path} --scaling_method \"{scaling_method}\" --exp_id {str(i)} {seed_str} {strong_targeted_str} &"
        print(cmd)