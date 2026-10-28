use riscv_emu_rust::{terminal::Terminal, Emulator};
use std::{cell::RefCell, io::Write, rc::Rc, time::Instant};

struct Console(Rc<RefCell<Vec<u8>>>);
impl Terminal for Console {
    fn put_byte(&mut self, byte: u8) {
        let mut tail = self.0.borrow_mut();
        tail.push(byte);
        if byte == b'\n' {
            let start = tail[..tail.len()-1].iter().rposition(|b| *b == b'\n').map_or(0, |i| i+1);
            std::io::stdout().write_all(&tail[start..]).unwrap();
            std::io::stdout().flush().unwrap();
        }
        if tail.len() > 65536 { tail.drain(..32768); }
    }
    fn get_output(&mut self) -> u8 { 0 }
    fn get_input(&mut self) -> u8 { 0 }
    fn put_input(&mut self, _: u8) {}
}

fn main() {
    let args: Vec<_> = std::env::args().collect();
    assert_eq!(args.len(), 3, "usage: enclave-risc-boot-test firmware.elf rootfs.ext2");
    let output = Rc::new(RefCell::new(Vec::new()));
    let mut emu = Emulator::new(Box::new(Console(output.clone())));
    emu.setup_ram_bytes(512 * 1024 * 1024);
    emu.setup_program(std::fs::read(&args[1]).unwrap());
    emu.setup_filesystem(std::fs::read(&args[2]).unwrap());
    let start = Instant::now();
    let marker = b"ENCLAVE_RISC_ALPINE_BOOT_OK";
    let mut instructions = 0u64;
    loop {
        emu.run_n(100_000);
        instructions += 100_000;
        if output.borrow().windows(marker.len()).any(|w| w == marker) {
            println!("PASS: real RISC Box emulator booted Alpine after {instructions} scheduled ticks in {:?}", start.elapsed());
            break;
        }
        assert!(instructions < 5_000_000_000 && start.elapsed().as_secs() < 600,
                "RISC Box Alpine boot did not reach its required marker");
    }
}
