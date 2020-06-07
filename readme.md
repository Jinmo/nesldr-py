	
# Nintendo Entertainment System (NES) loader module

Author: [@patois](https://github.com/patois), 
ported to IDAPython by: [@Jinmo](https://github.com/Jinmo)

IDA Pro loader module for Nintendo Enternainment System (NES) ROM images in iNES file format.

Please note that the real NES hardware memory area ends after 0xFFFF as it can address 16bit only.
The NES hardware uses several page/bank swapping mechanisms in order to load additional ROM banks.
This loader loads a maximum number of two 16k PRG ROM banks into the IDA database, respecting the original memory layout.
This significantly improves the disassembly on the one hand, but as a consequence doesn't allow the ROM to be reassembled in one step on the other.

## Installation
Copy the loader to %idadir%/loaders/nes.py, and %idadir%/loaders/nesldr.

## Information for developers
A copy of the input file is stored within the IDA Pro database by the loader. This allows all parts of the ROM to be accessed 
via netnodes.

### Example:

The original iNES header is stored in a netnode (INES_HDR_NODE). It can be accessed programmatically by reading the netnode's blob as shown below.

```
#include "nes.h"

netnode node(INES_HDR_NODE);
ines_hdr hdr;

node.getblob(&hdr, &INES_HDR_SIZE, 0, 'I');
```
