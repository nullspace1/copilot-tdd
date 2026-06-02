

from src import git
import src.print as print_module
import src.spec as spec
import src.status as status
import src.tdd_state as tdd_state



def main():
    
    spec_name = spec.spec_from_config()
    current_status_data = status.current_status(spec_name)
    
    return_to : status.Stage | None = status.check_return(current_status_data)
    
    if return_to:
        
        try:
            
            state : tdd_state.TDDState = tdd_state.copy_tdd_state(spec_name)

            state = tdd_state.add_iteration_to_history(spec_name, state)
            
            git.create_branch(f"tdd/{spec_name}-revision-{current_status_data['revision']}")
            git.add(".")
            git.commit(f"tdd({spec_name}): preserve revision {current_status_data['revision']}")
            
            git.switch_branch(f"tdd/{spec_name}")
            tdd_state.reset_to_stage(spec_name, return_to)
           
            tdd_state.paste_tdd_state(spec_name, state)
            tdd_state.add_feedback_from(spec_name, current_status_data['stage'], state)
            
            current_status_data['revision'] += 1
            current_status_data['stage'] = return_to
            current_status_data['result'] = 'read_feedback'
            
            status.write_status(spec_name, current_status_data)

            tdd_state.commit_stage(spec_name, return_to, f"tdd({spec_name}): return to {return_to}") 
            
            print_module.print_prompt({
                "status": "return to",
                "message": f"Return to {return_to} confirmed."
            })
            
            tdd_state.commit_stage(spec_name, current_status_data['stage'], f"tdd({spec_name}): return to {return_to}")
        except git.GitError as error:
            print_module.print_prompt({
                "status": "error",
                "message": f"Git error: {error.stderr}. Warn orchestrator agent"
            })
            return
        
    else: 

        if (current_status_data["result"] != "success"):
            print_module.print_prompt(
                {
                    "status": "error",
                    "message": f"Current stage {current_status_data['stage']} has not been completed successfully. Please be sure to update the status before proceeding."
                }
            )

        new_status = status.next_stage(current_status_data)
        status.write_status(spec_name, status.status(new_status, "start", current_status_data["revision"]))
        
        tdd_state.commit_stage(spec_name, current_status_data['stage'], f"tdd({spec_name}): starting {current_status_data['stage']} stage")
   
        print_module.print_prompt(
            {
                "status": "finished",
                "message": f"Your turn as the {current_status_data['stage']} agent is over. Please communicate your success to the orchestrator."
            }
        )
        
        
if __name__ == "__main__":
    main()