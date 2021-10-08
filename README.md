# cloud-hypervisor-tools
## chimg
Cloud Hypervisor tools for VM image compatibility.

Installation:
```bash
$ pip3 install .
$ ~/.local/bin/chimg -?
```

Retrieve image information:
```
$ chimg info /path/to/image
```

Convert to Cloud Hypervisor compatible format:
```
$ chimg convert /path/to/source [/path/to/target]
```

`chimg` will always operate on a copy of the supplied image. The copy is the original image converted to the RAW format.

