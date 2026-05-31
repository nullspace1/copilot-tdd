

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
            
            git.create_branch(f"feat/{spec_name}-revision-{current_status_data['revision']}")
            git.commit(f"tdd({spec_name}): preserve revision {current_status_data['revision']}")
            
            git.switch_branch(f"feat/{spec_name}")
            git.reset_hard(f"refs/tdd/{spec_name}/{return_to}")
            
            git.commit(f"tdd({spec_name}): return to {return_to}")
            
            tdd_state.paste_tdd_state(spec_name, state)
            tdd_state.add_feedback_from(spec_name, current_status_data['stage'], state)
            
            current_status_data['revision'] += 1
            current_status_data['stage'] = return_to
            current_status_data['result'] = 'read_feedback'
            
            status.write_status(spec_name, current_status_data)
            
            print_module.print_prompt({
                "status": "return to",
                "message": f"Return to {return_to} confirmed."
            })
            
            
        except git.GitError as error:
            print(error.stderr)
            return
        
    else: 
        
        print_module.print_prompt(
            {
                "status": "finished",
                "message": f"Your turn as a {current_status_data['stage']} is over."
            }
        )
        
        
if __name__ == "__main__":
    main()