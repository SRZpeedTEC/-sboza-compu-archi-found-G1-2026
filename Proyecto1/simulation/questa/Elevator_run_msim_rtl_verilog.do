transcript on
if {[file exists rtl_work]} {
	vdel -lib rtl_work -all
}
vlib rtl_work
vmap work rtl_work

vlog -sv -work work +incdir+/home/srobles/Desktop/Repos/-sboza-compu-archi-found-G1-2025/Proyecto1/Buzzer {/home/srobles/Desktop/Repos/-sboza-compu-archi-found-G1-2025/Proyecto1/Buzzer/flipflopD.sv}
vlog -sv -work work +incdir+/home/srobles/Desktop/Repos/-sboza-compu-archi-found-G1-2025/Proyecto1/Demos {/home/srobles/Desktop/Repos/-sboza-compu-archi-found-G1-2025/Proyecto1/Demos/mic_demo.sv}
vlog -sv -work work +incdir+/home/srobles/Desktop/Repos/-sboza-compu-archi-found-G1-2025/Proyecto1/Demos {/home/srobles/Desktop/Repos/-sboza-compu-archi-found-G1-2025/Proyecto1/Demos/elevator_demo_top.sv}
vlog -sv -work work +incdir+/home/srobles/Desktop/Repos/-sboza-compu-archi-found-G1-2025/Proyecto1/Demos {/home/srobles/Desktop/Repos/-sboza-compu-archi-found-G1-2025/Proyecto1/Demos/debounce.sv}
vlog -sv -work work +incdir+/home/srobles/Desktop/Repos/-sboza-compu-archi-found-G1-2025/Proyecto1/Helpers {/home/srobles/Desktop/Repos/-sboza-compu-archi-found-G1-2025/Proyecto1/Helpers/flip_flop_d.sv}
vlog -sv -work work +incdir+/home/srobles/Desktop/Repos/-sboza-compu-archi-found-G1-2025/Proyecto1/Helpers {/home/srobles/Desktop/Repos/-sboza-compu-archi-found-G1-2025/Proyecto1/Helpers/binary_counter.sv}
vlog -sv -work work +incdir+/home/srobles/Desktop/Repos/-sboza-compu-archi-found-G1-2025/Proyecto1/Microphone/modules {/home/srobles/Desktop/Repos/-sboza-compu-archi-found-G1-2025/Proyecto1/Microphone/modules/mic_top.sv}
vlog -sv -work work +incdir+/home/srobles/Desktop/Repos/-sboza-compu-archi-found-G1-2025/Proyecto1/Microphone/modules {/home/srobles/Desktop/Repos/-sboza-compu-archi-found-G1-2025/Proyecto1/Microphone/modules/mic_saver.sv}
vlog -sv -work work +incdir+/home/srobles/Desktop/Repos/-sboza-compu-archi-found-G1-2025/Proyecto1/Microphone/modules {/home/srobles/Desktop/Repos/-sboza-compu-archi-found-G1-2025/Proyecto1/Microphone/modules/mic_control_fsm.sv}
vlog -sv -work work +incdir+/home/srobles/Desktop/Repos/-sboza-compu-archi-found-G1-2025/Proyecto1/Buzzer {/home/srobles/Desktop/Repos/-sboza-compu-archi-found-G1-2025/Proyecto1/Buzzer/incrementer.sv}
vlog -sv -work work +incdir+/home/srobles/Desktop/Repos/-sboza-compu-archi-found-G1-2025/Proyecto1/Buzzer {/home/srobles/Desktop/Repos/-sboza-compu-archi-found-G1-2025/Proyecto1/Buzzer/counter.sv}
vlog -sv -work work +incdir+/home/srobles/Desktop/Repos/-sboza-compu-archi-found-G1-2025/Proyecto1/Buzzer {/home/srobles/Desktop/Repos/-sboza-compu-archi-found-G1-2025/Proyecto1/Buzzer/comparator.sv}
vlog -sv -work work +incdir+/home/srobles/Desktop/Repos/-sboza-compu-archi-found-G1-2025/Proyecto1/Buzzer {/home/srobles/Desktop/Repos/-sboza-compu-archi-found-G1-2025/Proyecto1/Buzzer/buzzer_top.sv}
vlog -sv -work work +incdir+/home/srobles/Desktop/Repos/-sboza-compu-archi-found-G1-2025/Proyecto1/Buzzer {/home/srobles/Desktop/Repos/-sboza-compu-archi-found-G1-2025/Proyecto1/Buzzer/buzzer_fsm.sv}
vlog -sv -work work +incdir+/home/srobles/Desktop/Repos/-sboza-compu-archi-found-G1-2025/Proyecto1/Buzzer {/home/srobles/Desktop/Repos/-sboza-compu-archi-found-G1-2025/Proyecto1/Buzzer/beep_counter.sv}
vlog -sv -work work +incdir+/home/srobles/Desktop/Repos/-sboza-compu-archi-found-G1-2025/Proyecto1/ALU {/home/srobles/Desktop/Repos/-sboza-compu-archi-found-G1-2025/Proyecto1/ALU/ALU_Substractor.sv}
vlog -sv -work work +incdir+/home/srobles/Desktop/Repos/-sboza-compu-archi-found-G1-2025/Proyecto1/ALU {/home/srobles/Desktop/Repos/-sboza-compu-archi-found-G1-2025/Proyecto1/ALU/ALU_Adder.sv}
vlog -sv -work work +incdir+/home/srobles/Desktop/Repos/-sboza-compu-archi-found-G1-2025/Proyecto1/ALU {/home/srobles/Desktop/Repos/-sboza-compu-archi-found-G1-2025/Proyecto1/ALU/ALU.sv}
vlog -sv -work work +incdir+/home/srobles/Desktop/Repos/-sboza-compu-archi-found-G1-2025/Proyecto1 {/home/srobles/Desktop/Repos/-sboza-compu-archi-found-G1-2025/Proyecto1/elevator_fsm.sv}

