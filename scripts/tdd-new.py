
from csv import Error

import src.git as git
import src.parse as parse
import src.print as print_module
import src.spec as spec
import src.status as status
import src.config as config


def main() -> None:
    
    prompt : str  = parse.load_prompt()
    
    if (parse.is_new_spec(prompt)):
        
        prompt = parse.parse_spec(prompt)
        
        config.save({"spec": prompt})
        
        try:
            spec.create_spec(prompt)
        except Exception as error:
            print_module.print_prompt({
                "status": "error",
                "error_message": str(error),
                "message": f"Error creating spec {prompt}. Warn user and provide a guide on how to restore state."
            })
            return
          
        spec.write_spec_to_config(prompt)
           
        print_module.print_prompt({
            "status": "new spec",
            "message": f"Spec {prompt} has been created. Please begin process"
        })
        
    else: 
        
        spec_name = spec.spec_from_config()
        status_data = status.current_status(prompt)
        
        
        if status.status_ended(status_data):
            print_module.print_prompt({
                "spec": spec_name,
                "status": "success",
                "message": f"Spec {prompt} has been completed successfully. Please notify user."
            })
        
        print_module.print_prompt({
            "spec": spec_name,
            "status": status_data["stage"],
            "result": status_data["result"],
            "revision": status_data["revision"],
            "message": "Continue process according to user input."
        })
        
if __name__ == "__main__":
    main()