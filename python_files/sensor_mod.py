"""
sensor_mod.py

This module interfaces with LEGO devices, processes sensor data, and displays 
it on a web interface.

Note: when doing the eval, we are hiding it using 'hidden'
This just means that it won't show in the REPL (debug) but it is still there

Authors: Javier Laveaga and William Goldman

Updated to use uboard instead of terminal
Optimized to prevent image flashing by separating layout creation from data updates

"""

import my_globals
import asyncio
from pyscript import document
import time
import helper_mod

#Ids of LEGO devices
device_names = {
    48: "medium_motor",
    49: "big_motor",
    61: "color_sensor",
    62: "distance_sensor",
    63: "force_sensor",
    64: "light_matrix",
    65: "small_motor"
    
}

#making 
port_names = {
    0: 'A',
    1: 'B',
    2: 'C',
    3: 'D',
    4: 'E',
    5: 'F'
}

# Keep track of current sensor layout to avoid unnecessary rebuilds
current_sensor_layout = {}

#code that gets pasted when on connecting
sensor_code = """

import device
import motor
import color_sensor
import color
import distance_sensor
import force_sensor

#test this
def big_motor_print(port_num):
    print("big_motor", port_num)
    abs_pos = motor.absolute_position(port_num)
    if (abs_pos < 0):
        abs_pos = abs_pos + 360
    return abs_pos

#color.RED = 1
#9 colors:
''' 
Table 1:

Red - 1
Green - 2
Blue - 3
Magenta - 4
Yellow 5
Orange - 6
Azure - 7 
Black - 8
White - 9

'''
#returns tuple with (color from table 1, r, g , b)
def color_sensor_print(port_num):
    #print("color sensor", port_num)
    color_info = [-1,-1,-1,-1] #tuple with, color, r,g,b values 
    #variable I will use to identify color based on Table 1
    my_color = -1 #if not color is detected
    sensor_color = color_sensor.color(port_num) #color that sensor detects
    if sensor_color is color.RED:
        my_color = 1
    elif sensor_color is color.GREEN:
        my_color = 2
    elif sensor_color is color.BLUE:
        my_color = 3
    elif sensor_color is color.MAGENTA:
        my_color = 4
    elif sensor_color is color.YELLOW:
        my_color = 5
    elif sensor_color is color.ORANGE:
        my_color = 6
    elif sensor_color is color.AZURE:
        my_color = 7
    elif sensor_color is color.BLACK:
        my_color = 8
    elif sensor_color is color.WHITE:
        my_color = 9

    return my_color
    
def distance_sensor_print(port_num):
    #print("distance sensor", port_num)
    return distance_sensor.distance(port_num)
    
def force_sensor_print(port_num):
    #print("force sensor", port_num)
    return force_sensor.force(port_num)
    
    
def light_matrix_print(port_num):
    #print("light matrix", port_num)
    return 1 #change this

#test this
def small_motor_print(port_num):
    #print("small motor", port_num)
    abs_pos = motor.absolute_position(port_num)
    if (abs_pos < 0):
        abs_pos = abs_pos + 360
    return abs_pos

#absolute position goes like 0...179, -180, -179 = vals
#want 0...179, 180, 181,... 360 (then go back to 0)
#so return 360 + val
def medium_motor_print(port_num):
    #print("medium motor", port_num)
    abs_pos = motor.absolute_position(port_num)
    if (abs_pos < 0):
        abs_pos = abs_pos + 360
    return abs_pos

function_dict = {
    48: medium_motor_print,
    49: big_motor_print,
    61: color_sensor_print,
    62: distance_sensor_print,
    63: force_sensor_print,
    64: light_matrix_print,
    65: small_motor_print
}

port_info = [()] * 6

"""

#tuple = (1 if connected & recognized, port number, sensor_id, number)
#Code that executes (eval) on every instance of sensor while loop
execute_code = """
    for i in range(6):
        #for each port get the device Id
        current_port = i
        try:
            #below is line that will give you error (potentially)
            port_id = device.id(current_port) #this should be either 49,61,62...
            # Call the corresponding function if the device ID is found
            if port_id in function_dict:
                number = function_dict[port_id](i)
                port_info[i] = (1, i, port_id, number)
            else:
                #print(f"No function defined for device ID {port_id}")
                port_info[i] = (0,0,0,0)
        except OSError as e: #nothing connected to it
            # Means port does not have any sensor connected to it
            port_info[i] = (0,0,0,0)
            #print("YAA")
            #print(f"Port {current_port} error: {e}")

port_info


"""


def create_sensor_layout(port_info_array):
    """
    Creates the initial HTML layout for sensors. Only called when sensor configuration changes.
    
    Args:
        port_info_array (list): Array of sensor information tuples
        
    Returns:
        str: HTML string for the sensor layout
    """
    sensor_info_html = "<div class='sensor-info-container'>"
    
    for t in port_info_array:
        if t[0] == 1:  # if something is connected to port
            port_name = port_names[t[1]]
            port_id = f"port-{t[1]}"
            
            if t[2] == 61:  # color sensor
                sensor_info_html += f"""
                <div class="sensor-info" id="{port_id}">
                    <div class="sensor-info-item">
                        <div class="sensor-stack-left">
                            <span class="port-name">{port_name}</span>
                        </div>
                        <div class="sensor-stack-right">
                            <span>
                                <img src="images/spike color_sensor_display.png" alt="color sensor">
                            </span>
                            <span class="sensor-value">
                                <div class="colorCircle" id="{port_id}-color" style="background-color: unknown;"></div>
                                <span id="{port_id}-text">Unknown</span>
                            </span>
                        </div>
                    </div>
                </div>
                """
            elif t[2] in [48, 49, 65]:  # motors
                sensor_info_html += f"""
                <div class="sensor-info" id="{port_id}">
                    <div class="sensor-info-item">
                        <div class="sensor-stack-left">
                            <span class="port-name">{port_name}</span>
                        </div>
                        <div class="sensor-stack-right">
                            <span><img src="images/spike medium_motor_display.png" alt="Motor"></span>
                            <span class="sensor-value" id="{port_id}-value">0 °</span>
                        </div>
                    </div>
                </div>
                """
            elif t[2] == 62:  # distance sensor
                sensor_info_html += f"""
                <div class="sensor-info" id="{port_id}">
                    <div class="sensor-info-item">
                        <div class="sensor-stack-left">
                            <span class="port-name">{port_name}</span>
                        </div>
                        <div class="sensor-stack-right">
                            <span><img src="images/spike distance_sensor_display.png" alt="distance sensor"></span>
                            <span class="sensor-value" id="{port_id}-value">0 mm</span>
                        </div>
                    </div>
                </div>
                """
            elif t[2] == 63:  # force sensor
                sensor_info_html += f"""
                <div class="sensor-info" id="{port_id}">
                    <div class="sensor-info-item">
                        <div class="sensor-stack-left">
                            <span class="port-name">{port_name}</span>
                        </div>
                        <div class="sensor-stack-right">
                            <span><img src="images/spike push_sensor_display.png" alt="force sensor"></span>
                            <span class="sensor-value" id="{port_id}-value">0 N</span>
                        </div>
                    </div>
                </div>
                """
            elif t[2] == 64:  # light matrix
                sensor_info_html += f"""
                <div class="sensor-info" id="{port_id}">
                    <div class="sensor-info-item">
                        <div class="sensor-stack-left">
                            <span class="port-name">{port_name}</span>
                        </div>
                        <div class="sensor-stack-right">
                            <span><img src="images/spike light_matrix_display.png" alt="light matrix"></span>
                            <span class="sensor-value" id="{port_id}-value">1</span>
                        </div>
                    </div>
                </div>
                """
    
    sensor_info_html += "</div>"
    return sensor_info_html


def update_sensor_values(port_info_array):
    """
    Updates only the sensor values without rebuilding the layout.
    
    Args:
        port_info_array (list): Array of sensor information tuples
    """
    color_detected = ["Red", "Green", "Blue", "Magenta", 
                      "Yellow", "Orange", "Azure", "Black", "White", "Unknown"]
    
    for t in port_info_array:
        if t[0] == 1:  # if something is connected to port
            port_id = f"port-{t[1]}"
            number = t[3]
            
            if t[2] == 61:  # color sensor
                color_name = (
                    color_detected[number - 1] 
                    if 0 < number <= len(color_detected) else "Unknown"
                )
                
                # Update color circle and text
                color_element = document.getElementById(f"{port_id}-color")
                text_element = document.getElementById(f"{port_id}-text")
                
                if color_element and text_element:
                    color_element.style.backgroundColor = color_name.lower()
                    text_element.innerText = color_name
                    
            elif t[2] in [48, 49, 65]:  # motors
                value_element = document.getElementById(f"{port_id}-value")
                if value_element:
                    value_element.innerText = f"{number} °"
                    
            elif t[2] == 62:  # distance sensor
                value_element = document.getElementById(f"{port_id}-value")
                if value_element:
                    value_element.innerText = f"{number} mm"
                    
            elif t[2] == 63:  # force sensor
                value_element = document.getElementById(f"{port_id}-value")
                if value_element:
                    value_element.innerText = f"{number} N"
                    
            elif t[2] == 64:  # light matrix
                value_element = document.getElementById(f"{port_id}-value")
                if value_element:
                    value_element.innerText = str(number)


def sensors_layout_changed(new_layout, old_layout):
    """
    Check if the sensor configuration has changed.
    
    Args:
        new_layout (list): New sensor configuration
        old_layout (dict): Previous sensor configuration
        
    Returns:
        bool: True if layout changed, False otherwise
    """
    # Create a simplified representation for comparison
    new_config = {}
    for t in new_layout:
        if t[0] == 1:  # connected
            new_config[t[1]] = t[2]  # port -> sensor_type
    
    return new_config != old_layout


#sensor_info and get terminal in same button
async def on_sensor_info(event):
    """
    Handles sensor information display logic, toggles between sensor info and terminal view.
    Optimized to prevent image flashing by only updating values, not rebuilding layout.

    Args:
        event (Event): The event triggering the sensor information display.
    """
    print("ON-SENSOR")  
    global current_sensor_layout

    my_globals.stop_loop = False

    # next time sensors clicked, will hide sensor info
    my_globals.sensors.onclick = close_sensor
    sensor = False #so that on next click it displays terminal

    # sensors.innerText = 'Get Terminal'
    my_globals.sensors.innerText = 'Close'
    
    print("STOP-LOOP", my_globals.stop_loop)
    
    # Flag to track if we need to rebuild the layout
    layout_built = False

    while not my_globals.stop_loop:
        # Updated to use uboard instead of terminal
        try:
            port_info_array = await my_globals.uboard.eval(execute_code, hidden=True)
        except Exception as e:
            print(f"Error evaluating sensor code: {e}")
            break

        # Check if sensor configuration changed
        if sensors_layout_changed(port_info_array, current_sensor_layout) or not layout_built:
            print("Sensor layout changed, rebuilding...")
            # Update current layout tracking
            current_sensor_layout = {}
            for t in port_info_array:
                if t[0] == 1:
                    current_sensor_layout[t[1]] = t[2]
            
            # Rebuild the entire layout
            sensor_info_html = create_sensor_layout(port_info_array)
            document.getElementById('sensor-info').innerHTML = sensor_info_html
            layout_built = True
        else:
            # Just update the values
            update_sensor_values(port_info_array)

        print("In LOOP ")

        # Add a small delay to prevent overwhelming the system
        await asyncio.sleep(0.1)

    print("STOP-LOOP True")


#called when displaying all sensors except the color sensor
def display_sensors(source, alt, number, port_name, unit, sensor_info_html):
    """
    Updates the sensor information HTML content for non-color sensors.
    DEPRECATED: This function is kept for backward compatibility but is no longer used
    in the optimized version.

    Args:
        source (str): The image source for the sensor.
        alt (str): The alt text for the sensor image.
        number (int): The sensor value.
        port_name (str): The name of the port.
        unit (str): The unit of measurement for the sensor value.
        sensor_info_html (str): The current HTML content for sensor information.

    Returns:
        str: Updated HTML content for sensor information.
    """
    sensor_info_html += f"""
    <div class="sensor-info">
        <div class="sensor-info-item">
            <div class="sensor-stack-left">
                <span class="port-name">{port_name}</span>
            </div>
            <div class="sensor-stack-right">
                <span><img src="{source}" alt="{alt}"></span>
                <span class="sensor-value">{number} {unit}</span>
            </div>
        </div>
    </div>
    """
    return sensor_info_html


def display_color_sensor(port_name, color_name, color_array, number, 
                         sensor_info_html):
    """
    Updates the sensor information HTML content for the color sensor.
    DEPRECATED: This function is kept for backward compatibility but is no longer used
    in the optimized version.

    Args:
        port_name (str): The name of the port.
        color_name (str): The name of the detected color.
        color_array (list): List of known color names.
        number (int): The index of the detected color in the color_array.
        sensor_info_html (str): The current HTML content for sensor information.

    Returns:
        str: Updated HTML content for sensor information.
    """
    sensor_info_html += f"""
    <div class="sensor-info">
        <div class="sensor-info-item">
            <div class="sensor-stack-left">
                <span class="port-name">{port_name}</span>
            </div>
            <div class="sensor-stack-right">
                <span>
                <img 
                src="images/spike color_sensor_display.png" alt="color sensor">
                </span>
                <span class="sensor-value">
                    <div 
                    class="colorCircle" style="background-color: {color_name};">
                    </div>
                    {color_array[number - 1]}
                </span>
            </div>
        </div>
    </div>
    """
    return sensor_info_html


async def close_sensor(event=None):
    """
    Closes the sensor information display and re-enables other buttons.

    Args:
        event (Event, optional): The event triggering the sensor information 
        closure.
    """
    global current_sensor_layout
    
    print("In_CLose")
    #class button1 disabling
    helper_mod.disable_buttons([my_globals.sensors, my_globals.download, 
                    my_globals.custom_run_button, my_globals.upload_file_btn, 
                    my_globals.save_btn, my_globals.connect, 
                    my_globals.file_list, my_globals.debug_btn, my_globals.terminal_btn])
    my_globals.stop_loop = True
    
    # Reset layout tracking
    current_sensor_layout = {}
    
    #(min of 0.32 - worst case scenario (when you trigger stop_loop boolean
    #in close sensor right before calling eval in while loop of on_sensor info))
    await asyncio.sleep(0.5) #allow while loop to finish its current iteration 

    # next time sensors clicked, will hide sensor info
    my_globals.sensors.onclick = on_sensor_info
    document.getElementById('sensor-info').innerHTML = " "
    print("CLEARED")
    my_globals.sensors.innerText = 'Sensors'
    print("REACHED")
    #show terminal
    document.getElementById('repl').style.display = 'block'