# Retained streaming client

`source.json` pins the external Moonlight Qt client and the recovered audio/input
patch. It is built separately from the guest OS. The client workflow applies the
hash-checked patch to the exact recursive source revision, compiles the real Qt
application and checks the combined audio backlog boundary, including partial
frames, invalid values and overflow. Its CPU video configuration permits later
headless streaming tests without a physical GPU.

A successful compile or CLI startup does not qualify pairing, encrypted streaming,
audio continuity or desktop/menu/game cursor transitions. Those require an actual
Sunshine connection through each platform adapter. No existing local Moonlight
installation, pairing credential or live desktop is changed by this workflow.
