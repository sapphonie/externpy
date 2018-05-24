import keyboard
import pymem
import mouse
import time

local_offset = (0xCE32F0)
entity_offset = (0xCF0E3C)
team_offset = (0xB0)
flags_offset = (0x37C)
in_cross_offset = (0x177C)
force_attack = (0xD12114)
force_jump = (0xD12108)

pm = pymem.Pymem('hl2.exe')

def main():
    print('externpy')
 
    client = pymem.process.module_from_name(pm.process_id, 'client.dll')
    local = client.base_address + local_offset
    l_flags = pm.read_int(local) + flags_offset
    l_team = pm.read_int(local) + team_offset
    in_cross = pm.read_int(local) + in_cross_offset

    while True:
    	local_flags = pm.read_int(l_flags)
    	local_team = pm.read_int(l_team)
    	entity_index = pm.read_int(in_cross)

    	if mouse.is_pressed('right'):
    		if entity_index > 0 and entity_index <= 32:
    			ent = pm.read_int((client.base_address + entity_offset + (entity_index - 1) * 0x10))
    			if local_team != pm.read_int(ent + team_offset):
    				pm.write_int(client.base_address + force_attack, 5)
    				time.sleep(0.01)
    				pm.write_int(client.base_address + force_attack, 4)

    	if local_flags == 257 and keyboard.is_pressed('shift'):
    		pm.write_int(client.base_address + force_jump, 6)
    		time.sleep(0.01)

if __name__ == '__main__':
    main()
