import pymem
import time
import sys
import re
import struct

# TODO: warn that pattern is a regex and may need to be escaped
# TODO: 2.0 rename to pattern_scan_page
def scan_pattern_page(handle, address, pattern, *, return_multiple=False):
    """Search a byte pattern given a memory location.
    Will query memory location information and search over until it reaches the
    length of the memory page. If nothing is found the function returns the
    next page location.
    Parameters
    ----------
    handle: int
        Handle to an open object
    address: int
        An address to search from
    pattern: bytes
        A regex byte pattern to search for
    return_multiple: bool
        If multiple results should be returned instead of stopping on the first
    Returns
    -------
    tuple
        next_region, found address
        found address may be None if one was not found, or we didn't have permission to scan
        the region
        if return_multiple is True found address will instead be a list of found addresses
        or an empty list if no results
    Examples
    --------
    >>> pm = pymem.Pymem("Notepad.exe")
    >>> address_reference = 0x7ABC00001
    # Here the "." means that the byte can be any byte; a "wildcard"
    # also note that this pattern may be outdated
    >>> bytes_pattern = b".\\x00\\x00\\x00\\x01\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00" \\
    ...                 b"\\x00\\x00\\x00\\x00\\x00\\x00..\\x00\\x00..\\x00\\x00\\x64\\x04"
    >>> character_count_address = pymem.pattern.scan_pattern_page(pm.process_handle, address_reference, bytes_pattern)
    """
    mbi = pymem.memory.virtual_query(handle, address)
    next_region = mbi.BaseAddress + mbi.RegionSize
    allowed_protections = [
        pymem.ressources.structure.MEMORY_PROTECTION.PAGE_EXECUTE_READ,
        pymem.ressources.structure.MEMORY_PROTECTION.PAGE_EXECUTE_READWRITE,
        pymem.ressources.structure.MEMORY_PROTECTION.PAGE_READWRITE,
        pymem.ressources.structure.MEMORY_PROTECTION.PAGE_READONLY,
    ]
    if mbi.state != pymem.ressources.structure.MEMORY_STATE.MEM_COMMIT or mbi.protect not in allowed_protections:
        return next_region, None

    page_bytes = pymem.memory.read_bytes(handle, address, mbi.RegionSize)

    if not return_multiple:
        found = None
        match = re.search(pattern, page_bytes, re.DOTALL)

        if match:
            found = address + match.span()[0]

    else:
        found = []

        for match in re.finditer(pattern, page_bytes, re.DOTALL):
            found_address = address + match.span()[0]
            found.append(found_address)

    return next_region, found


def pattern_scan_module(handle, module, pattern, *, return_multiple=False):
    """Given a handle over an opened process and a module will scan memory after
    a byte pattern and return its corresponding memory address.
    Parameters
    ----------
    handle: int
        Handle to an open object
    module: MODULEINFO
        An instance of a given module
    pattern: bytes
        A regex byte pattern to search for
    return_multiple: bool
        If multiple results should be returned instead of stopping on the first
    Returns
    -------
    int, list, optional
        Memory address of given pattern, or None if one was not found
        or a list of found addresses in return_multiple is True
    Examples
    --------
    >>> pm = pymem.Pymem("Notepad.exe")
    # Here the "." means that the byte can be any byte; a "wildcard"
    # also note that this pattern may be outdated
    >>> bytes_pattern = b".\\x00\\x00\\x00\\x01\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00" \\
    ...                 b"\\x00\\x00\\x00\\x00\\x00\\x00..\\x00\\x00..\\x00\\x00\\x64\\x04"
    >>> module_notepad = pymem.process.module_from_name(pm.process_handle, "Notepad.exe")
    >>> character_count_address = pymem.pattern.pattern_scan_module(pm.process_handle, module_notepad, bytes_pattern)
    """
    base_address = module.lpBaseOfDll
    max_address = module.lpBaseOfDll + module.SizeOfImage
    page_address = base_address

    if not return_multiple:
        found = None
        while page_address < max_address:
            page_address, found = scan_pattern_page(handle, page_address, pattern)

            if found:
                break

    else:
        found = []
        while page_address < max_address:
            page_address, new_found = scan_pattern_page(handle, page_address, pattern, return_multiple=True)

            if new_found:
                found += new_found

    return found

pm = pymem.Pymem('hl2.exe')

def main():
    print('yo mama')
    print(pm)
    engine      = pymem.process.module_from_name( pm.process_handle, 'engine.dll' )
    enginebase  = pymem.process.module_from_name( pm.process_handle, 'engine.dll' ).lpBaseOfDll
    
    print('engbase =', enginebase)

    Net_SendPacket_Sig = b"\x55\x8B\xEC\xB8\x88\x20\x00\x00"
    Net_SendPacket_Loc = pattern_scan_module( pm.process_handle, engine, Net_SendPacket_Sig, return_multiple=False )
    print("SENDPACKETLOC = ", Net_SendPacket_Loc)

    # Allocate some space for our trampoline
    detour_ptr = pm.allocate(256)
    
    print(hex(detour_ptr))
    # flip that mfer around
    detour_endian = struct.pack( '<I', detour_ptr )
    print(detour_endian)

    ljmp    = b'\xff\x2d'
    nop     = b'\x90'
    ret     = b'\xC3'

    mov     = b'\xb8'
    calleax = b'\xff\xd0'
    bytepatch = mov + detour_endian + calleax + nop

    print(bytepatch.hex())
    pm.write_bytes( Net_SendPacket_Loc, bytepatch, 8 )


    bytes = ( pm.read_bytes( Net_SendPacket_Loc, 16 ) ).hex()
    print(bytes)

    pm.write_bytes( detour_ptr, ret, 1 )
    bytes = ( pm.read_bytes( detour_ptr, 16 ) ).hex()

    print(bytes)


    # while True
    #   idk

if __name__ == '__main__':
    main()




