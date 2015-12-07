import sys
import random

def blockrest():
    blockrestdata = ""
    for i in range(0,128-8):
        blockrestdata+=chr(random.randint(0,255))
    return blockrestdata.encode("hex")


def fillblock(blocknr):
    blockheader = 'BLOCK  %08X\n' % blocknr
    blockcontent = blockrest()
    return blockheader + blockcontent + blockheader + blockcontent

def filldisk(filename, lengthinblocks, seed):
    random.seed(seed)
    with open(filename,"w") as f:
        for blocknr in range(0,lengthinblocks):
            f.write(fillblock(blocknr))

filldisk(sys.argv[1],int(sys.argv[2]),int(sys.argv[3]))
