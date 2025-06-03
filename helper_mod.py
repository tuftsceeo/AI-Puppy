"""
helper_mod.py

Authors: Javier Laveaga, William Goldman

This script handles various operations for interacting with the Spike Prime 
board, including stopping code execution, cleaning up after disconnection, 
removing files, selecting files, handling board events, and enabling/disabling 
buttons.

Updated to use uboard instead of terminal system.
"""

from js import console
console.log("HERE 1")

from pyscript import document, window
import my_globals
import print_jav
import sensor_mod
import file_os
import asyncio
import my_gif

console.log("HERE 2")

async def stop_running_code():
    """
    Stops the currently running code, performs necessary cleanup, 
    and updates the UI.

    This function stops the code execution on the Spike Prime, updates 
    the status in the UI, re-enables the buttons, and clears any displayed gifs.
    It assumes that the uboard is connected and that necessary global 
    variables are updated accordingly.

    Raises:
        None

    Returns:
        None
    """
    my_globals.isRunning = False
    my_globals.found_key = False
    if my_globals.uboard.connected:
        try:
            my_gif.display_gif("") #clear gifs when stop running
            # Send keyboard interrupt to stop running code
            await my_globals.uboard.board.eval('\x03')
            
            # Add small delay to allow board to process interrupt
            await asyncio.sleep(0.5)
            
            # Clear any potential pending output
            await my_globals.uboard.board.eval('', timeout=0.1)
            
            print_jav.print_custom_terminal("Code execution ended. Please press the button to run the code again.")
            
            enable_buttons([my_globals.sensors, my_globals.download, 
                          my_globals.custom_run_button, my_globals.save_btn, 
                          my_globals.upload_file_btn, my_globals.connect,
                          my_globals.file_list, my_globals.debug_btn, 
                          my_globals.terminal_btn])

            await sensor_mod.on_sensor_info(None) #display sensors
            print('stopped code successfully')
            
        except Exception as e:
            print(f"Error stopping code: {e}")
            print_jav.print_custom_terminal("Error stopping code. Trying to recover...")
            # Attempt to recover by reconnecting
            try:
                await my_globals.uboard.board.disconnect()
                await asyncio.sleep(1)
                stop = True  # equivalent to 'repl' mode
                await my_globals.uboard.board.connect('repl', stop)
                print_jav.print_custom_terminal("Recovered connection. You can now run code again.")
            except Exception as reconnect_error:
                print(f"Recovery failed: {reconnect_error}")
                print_jav.print_custom_terminal("Could not recover connection. Please reconnect manually.")
        
        window.fadeImage('') #do this to clear gifs

async def debugging_time():
    """
    Enable debugging mode - disable certain buttons and enable terminal.
    """
    #disable file list 
    disable_buttons([my_globals.debug_btn, my_globals.terminal_btn,
                     my_globals.file_list])
    await sensor_mod.close_sensor()
    enable_buttons([my_globals.terminal_btn])
    my_globals.terminal_btn.style.backgroundColor = "red"

async def not_debugging():
    """
    Exit debugging mode - re-enable buttons and restore normal operation.
    """
    disable_buttons([my_globals.terminal_btn])
    enable_buttons([my_globals.debug_btn, my_globals.download, 
                    my_globals.sensors, my_globals.connect, 
                    my_globals.custom_run_button, my_globals.save_btn, 
                    my_globals.upload_file_btn, my_globals.file_list])
    my_globals.terminal_btn.style.backgroundColor = "#ccc"
    await sensor_mod.on_sensor_info(None)

def clean_up_disconnect():
    """
    Cleans up after a disconnection event, stops any running program, 
    and updates the UI.

    This function handles the disconnection of the Spike Prime, stops any 
    running program, updates the UI to reflect the disconnection, and 
    re-enables/disables appropriate buttons. 
    
    It is called by the disconnect callback in main.py (second_half_disconnect)

    Raises:
        None

    Returns:
        None
    """
    print("CLEANSHEESH")
    #if you are reading sensors and you physicaly disconnect
    if(my_globals.sensors.onclick == sensor_mod.close_sensor): 
        print_jav.print_custom_terminal("""Physically Disconnected while 
                                        reading sensors - RELOADING PAGE""")
        #reloads page
        document.getElementById(f"lesson{my_globals.lesson_num}-link").click() 
    
    if my_globals.uboard.connected:
        print('connected')
        print('after disconnect, passed x03')
        # Send keyboard interrupt to stop any running program
        asyncio.create_task(my_globals.uboard.board.eval('\x03'))
        # Disconnect the board
        asyncio.create_task(my_globals.uboard.board.disconnect())
    else:
        print("DISCONNECTED")
    
    if(my_globals.isRunning):
        #stops animation of run buttton (displaying purposes)
        document.getElementById('custom-run-button').click() 

    print_jav.print_custom_terminal("Disconnected from your Spike Prime.")

    #allow user to connect back
    my_globals.connect.innerText = 'Connect'
    disable_buttons([my_globals.sensors, my_globals.download, 
                     my_globals.custom_run_button, my_globals.save_btn, 
                     my_globals.upload_file_btn, my_globals.file_list,
                     my_globals.debug_btn, my_globals.terminal_btn])
    enable_buttons([my_globals.connect])

    #make the connect button green
    if (my_globals.connect.classList.contains('connected')):
        my_globals.connect.classList.remove('connected')

async def check_files():
    """
    Iterates through the list of files and checks to see if it contains
    the appropriate Main Lesson file and CEEO_AI.py. If it does, it
    opens the lesson file automatically on the editor. 

    If it doesn't it prompts you to click on download button with a warning

    Raises:
        None

    Returns:
        None
    """
   
    #important for resetting fading (avoids conflicts of having multiple
    # fadings at once)
    window.stopFadingWarningIcon() 
    # check to see if proper files are contained (Lesson file and CEEO)
    Lesson_file_found = False
    ceeo_file_found = False
    for i in range(my_globals.file_list.options.length - 1, -1, -1):
        option = my_globals.file_list.options.item(i)
        option_text = option.text
        if option_text == my_globals.proper_name_of_file[my_globals.lesson_num]:
            Lesson_file_found = True
        if option_text == "/flash/CEEO_AI.py":
            print("AQUIUIUUIIUI")
            ceeo_file_found = True
    
    if not Lesson_file_found or not ceeo_file_found:
        new_option = document.createElement('option')
        error_string = (
            "You do not have the right file. Please click the download button"
        )
        new_option.text = error_string
        window.startFadingWarningIcon() 
        my_globals.file_list.appendChild(new_option)
        #makes error_string be the 'file' that is selected
        my_globals.file_list.value = error_string
        print('end of if statement')
        enable_buttons([my_globals.sensors, my_globals.download, 
                my_globals.custom_run_button, my_globals.save_btn, 
                my_globals.upload_file_btn, my_globals.connect, 
                my_globals.file_list, my_globals.debug_btn, 
                my_globals.terminal_btn])
        await sensor_mod.on_sensor_info(None) #display sensors
    else:
        #so that the lesson file is displayed automatically
        my_globals.file_list.value = my_globals.proper_name_of_file[
                                            my_globals.lesson_num] 
        print('not empty')
        window.stopFadingWarningIcon()
        await on_select(None)  # Attempt to call on_select

async def on_select(event):
    """
    Handles the file selection event, attempts to read the selected file's code,
    and updates the editor.

    This function is triggered when a file is selected from the dropdown. 
    It attempts to read the code from the selected file and updates the editor 
    with the file's content. The function retries in case of errors up to a 
    maximum timeout count and updates the UI accordingly.

    Args:
        event (Event): The event object representing the file selection event.

    Raises:
        Exception: If reading the file's code fails repeatedly until 
        the timeout count is reached.

    Returns:
        None
    """
    await sensor_mod.close_sensor()
    print("on selectsiuu")
    #We are calling on_select multiple times until it doesn't give errors 
    # (usually it doesn't)
    timeout = 1  # Timeout duration in seconds (change this) 
    #**will remain in seconds if asyncion.sleep remains at 0.1
    timeout_count = 0
    max_timeout_count = 10 * timeout  # Adjust as necessary
    
    while True:
        try:
            my_globals.my_green_editor.code = await file_os.read_code(
                my_globals.uboard, my_globals.file_list)
            print("on_select completed successfully")
            break
        except Exception as e:
            print(f"An error occurred while calling on_select: {e}")
            timeout_count += 1
            print("TIMEOUT", timeout_count)
            if timeout is not None and timeout_count >= max_timeout_count:
                print("PROBLEM HERE")
                document.getElementById(
                    f"lesson{my_globals.lesson_num}-link").click() #reload page
                break
        
        #(this is why timeout is in seconds --> 0.1 * max_timeout_count = 1 sec)
        await asyncio.sleep(0.1)  # Short delay before retrying 
    enable_buttons([my_globals.sensors, my_globals.download, 
                    my_globals.custom_run_button, my_globals.save_btn, 
                    my_globals.upload_file_btn, my_globals.connect, 
                    my_globals.file_list, my_globals.debug_btn, 
                    my_globals.terminal_btn])
    await sensor_mod.on_sensor_info(None) #display sensors

#evaluates code when the green button is pressed
async def handle_board(event):
    """
    Handles the board event when the green run button is pressed 
    and evaluates the code.

    This function is triggered by an event, specifically when the custom run 
    button ('mpy-run') is pressed. It updates the global state, 
    disables certain buttons, displays a loading indicator, and sends code to 
    the uboard for evaluation. It also handles cases where the uboard 
    is not connected.

    Args:
        event (Event): The event object representing the button press, 
        containing details like the code to run.

    Raises:
        None

    Returns:
        bool: see below
    """
    if event.type == 'mpy-run': #even of hitting our custom run button
        my_globals.isRunning = True
        print("SIUUU")
        await sensor_mod.close_sensor()
        if my_globals.uboard.connected:
            disable_buttons([my_globals.sensors, my_globals.download, 
                             my_globals.custom_run_button, 
                             my_globals.upload_file_btn, my_globals.save_btn,
                             my_globals.debug_btn, my_globals.terminal_btn])
            print_jav.print_custom_terminal("Running code...")
            if my_globals.lesson_num == 3: #display this at the very beginning
                my_gif.display_gif("gifs/Lesson3/0gifsensor.gif")

            document.getElementById('gif').style.visibility = 'visible'
            document.getElementById('gif').style.display = 'block'
            code = event.detail.code
            
            try:
                # Use uboard's paste method - make sure we're using the board instance
                await my_globals.uboard.board.paste('\x05' + code + "#**END-CODE**#" + '\x04')
                print_jav.print_custom_terminal("Code pasted successfully!")
            except Exception as e:
                print(f"Error pasting code: {e}")
                print_jav.print_custom_terminal(f"Error running code: {str(e)}")
                # Re-enable buttons on error
                enable_buttons([my_globals.sensors, my_globals.download, 
                               my_globals.custom_run_button, my_globals.save_btn, 
                               my_globals.upload_file_btn, my_globals.connect,
                               my_globals.file_list, my_globals.debug_btn, 
                               my_globals.terminal_btn])
                return False
                
            my_globals.uboard.focus()
            enable_buttons([my_globals.custom_run_button])
            return False  #return False to avoid executing on browser
        else:
            print('uboard not connected')
            print_jav.print_custom_terminal("SPIKE Prime not connected. Please connect first.")
            return True
    # 'else' is needed only if using the default editor run button (we hid it)
    # else:
    #     code = event.code 

def disable_buttons(list_to_disable):
    """
    Disables a list of buttons and updates their display state.

    This function iterates over a list of button elements and disables them,
    preventing user interaction. It also updates the visual state of the buttons
    by adding a 'disabled' class to the 'custom-run-button' and removing the 
    'active' class from other buttons.

    Args:
        list_to_disable (list): A list of document elements representing buttons
        to be disabled.

    Returns:
        None
    """
    for element in list_to_disable:
        element.disabled = True #for actual functioning
        if element.id == 'custom-run-button':
            element.classList.add('disabled')  # add a 'disabled' class
        elif (element.classList.contains('button1')): #if you are a button 1
            element.classList.remove('active')

def enable_buttons(list_to_enable):
    """
    Enables a list of buttons and updates their display state.

    This function iterates over a list of button elements and enables them,
    allowing user interaction. It also updates the visual state of the buttons
    by removing the 'disabled' class from the 'custom-run-button' and adding 
    the 'active' class to other buttons.

    Args:
        list_to_enable (list): A list of document elements representing 
        buttons to be enabled.

    Returns:
        None
    """
    for element in list_to_enable:
        #controls actually being able to click and activate it/calling 
        #corresponding function
        element.disabled = False #includes disabling select
        if element.id == 'custom-run-button':
            element.classList.remove('disabled')  # remove the 'disabled' class
        elif (element.classList.contains('button1')): #if you are a button 1
            element.classList.add('active') #controls display for other buttons

async def on_save(event):
    """
    Handles the process of saving code from the editor and updating the user 
    interface.

    This function performs the following tasks:
    1. Closes any active sensors.
    2. Disables buttons to prevent user interaction during the save process.
    3. Saves the current code locally on the user's computer.
    4. Saves the code onto a SPIKE robot using uboard.
    5. Updates the user interface to reflect the saving status.
    6. Re-enables the buttons and updates the sensor display if the save is 
        not triggered by a disconnect event.

    Args:
        event (Event): The event object triggered by the save action. 
        This parameter is currently not used in the function but is required 
        for asynchronous handling.

    Returns:
        None
    """
    await sensor_mod.close_sensor()

    #SAVING LOCALLY
    my_editor_code = my_globals.my_green_editor.code #code in editor
    #get name of file that is currently selected (value)
    name_file = my_globals.file_list.value # "CEEO_AI.py" for example
    print("MY_option", name_file)
    #passing code and name of file (to save locally on computer)
    await my_globals.saving_js_module.save(my_editor_code, name_file)

    #SAVING ON SPIKE robot using uboard
    print_jav.print_custom_terminal("Saving code on SPIKE, please wait...")
    print_jav.print_custom_terminal("...")
    print_jav.print_custom_terminal("...")
    print_jav.print_custom_terminal("...")
    my_globals.progress_bar.style.display = 'block'
    
    try:
        # Use uboard's upload method instead of terminal.download
        status = await my_globals.uboard.board.upload(name_file, my_editor_code)
        if not status: 
            window.alert(f"""Failed to load {name_file}. 
                            Click Ok to continue downloading other files""")  
    except Exception as e:
        print(f"Error saving file: {e}")
        window.alert(f"Failed to save {name_file}: {str(e)}")
        status = False
    
    my_globals.progress_bar.style.display = 'none'
    print_jav.print_custom_terminal("Saved on SPIKE!")
    enable_buttons([my_globals.download, my_globals.sensors, 
                    my_globals.connect, my_globals.custom_run_button,
                    my_globals.save_btn, my_globals.upload_file_btn, 
                    my_globals.file_list, my_globals.debug_btn])
    await asyncio.sleep(0.1)  # allow download to finish before enabling sensors
    
    #only display sensors when save is called by clicking save button
    #prevents errors when calling save on disconnect
    if (not my_globals.save_on_disconnect):
        await sensor_mod.on_sensor_info(None) #display sensors (only call this)
        print("ENABLED BUTTONS ON SAVE")