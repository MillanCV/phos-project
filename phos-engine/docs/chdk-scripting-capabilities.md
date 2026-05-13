# CHDK Scripting Capabilities Reference

This document summarizes what you can do with CHDK scripting, based on the official CHDK Scripting Cross Reference and related CHDK scripting pages.

Primary reference:

- [CHDK Scripting Cross Reference Page](https://chdk.fandom.com/wiki/CHDK_Scripting_Cross_Reference_Page)
Supporting references:

- [Script commands](https://chdk.fandom.com/wiki/Script_commands)
- [CHDK scripting](https://chdk.fandom.com/wiki/CHDK_scripting)
- [Lua PTP scripting](https://chdk.fandom.com/wiki/Lua/PTP_Scripting)
- [Motion detection](https://chdk.fandom.com/wiki/Motion_Detection)
- [Lua raw hook operations](https://chdk.fandom.com/wiki/Lua/Raw_Hook_Operations)

## At a Glance

CHDK scripting gives you programmable control over:

- lens and focus behavior
- exposure and ISO/shutter/aperture overrides
- shooting and button simulation
- camera mode/state and configuration values
- motion detection triggers
- USB/PTP communication and remote capture
- RAW pipeline and raw buffer operations
- on-screen UI, drawing, and script console output
- file system / SD card information
- low-level firmware interaction (Lua)

Both Lua and uBASIC are supported for many commands, but Lua has broader capabilities in advanced areas (PTP messaging, drawing, raw hooks, firmware interfaces, memory operations, `imath`).

## Capability Catalog by Category

### 1) Lens and Focus

Core capabilities:

- read current focus distance and focus state (`get_focus`, `get_focus_state`, `get_focus_ok`)
- set focus distance and focus behavior (`set_focus`, `set_mf`, `set_aflock`)
- query and control zoom (`get_zoom`, `get_zoom_steps`, `set_zoom`, `set_zoom_rel`, `set_zoom_speed`)
- read image stabilization mode (`get_IS_mode`)
- use advanced focus override behavior on some models (`set_focus_interlock_bypass`, Lua only)

Use cases:

- focus lock for timelapse consistency
- manual focus scripting for stars/lightning
- focus stepping for focus stacking

### 2) Depth of Field (DOF)

Core capabilities:

- DOF metrics (`get_dofinfo` in Lua, plus uBASIC DOF helpers)
- near/far/hyperfocal calculations (`get_near_limit`, `get_far_limit`, `get_hyp_dist`)
- focal length queries (`get_focal_length`)

Use cases:

- fixed focus distance for landscape/night scenes
- verify sharpness zone before interval shooting

### 3) Exposure Control

Core capabilities:

- read measured values (`get_tv96`, `get_av96`, `get_sv96`, `get_bv96`, `get_ev`)
- set override values (`set_tv96`, `set_tv96_direct`, `set_av96`, `set_av96_direct`, `set_sv96`, `set_ev`)
- ISO control (`get_iso_mode`, `get_iso_real`, `set_iso_mode`, `set_iso_real`)
- user mode overrides (`set_user_tv96`, `set_user_av96`, by-id/by-relative-id variants)
- ND filter control (`get_nd_present`, `set_nd_filter`)
- exposure lock (`set_aelock`)
- live histogram/active imaging info (`get_live_histo`, `get_imager_active`, `get_current_tv96`, `get_current_av96`)

Use cases:

- scripted exposure bracketing
- low-light long exposure tuning
- ISO clamping during intervalometer runs

### 4) APEX96 and Unit Conversion Helpers

Core capabilities:

- ISO, `sv96`, `av96`, `tv96` conversion helpers (`iso_to_sv96`, `sv96_to_iso`, `tv96_to_usec`, `usec_to_tv96`, etc.)

Use cases:

- convert human units to scripting units reliably
- keep calculations deterministic across scripts

### 5) Camera State and Operating Mode

Core capabilities:

- query mode/state (`get_mode`, `get_movie_status`, `get_video_recording`, `get_drive_mode`, `get_flash_mode`)
- set camera mode (`set_record`, `set_capture_mode`, `set_capture_mode_canon`)
- read battery and temperature (`get_vbatt`, `get_temperature`)
- query camera capabilities (`get_video_button`, `is_capture_mode_valid`, raw support/image format functions)
- reboot/shutdown and script cleanup (`reboot`, `shut_down`, `restore`)

Use cases:

- preflight checks before trigger
- automated mode switching rec/playback
- health telemetry in long-running sessions

### 6) Keypad and Shutter Simulation

Core capabilities:

- key event simulation (`press`, `release`, `click`)
- shutter helpers (`shoot`, plus half/full press patterns via button commands)
- key state checks (`is_key`, `is_pressed`, `wait_click`)
- jog wheel simulation (`wheel_left`, `wheel_right`)
- configure script exit key (`set_exit_key`)

Use cases:

- emulate manual interaction from script
- robust scripted shooting flows with explicit half-press/full-press timing

### 7) SD Card and File-Related Info

Core capabilities:

- SD size/free space and shot counters (`get_disk_size`, `get_free_disk_space`, `get_jpg_count`, `get_raw_count`, `get_exp_count`)
- current image directory (`get_image_dir`, Lua)
- partition info and swapping (`get_partitionInfo`, `swap_partitions`)
- file attributes (`set_file_attributes`, Lua)

Use cases:

- pre-capture storage guards
- automated file planning and session limits

### 8) Script Runtime and Timing

Core capabilities:

- detect autostart state (`autostarted`, `get_autostart`, `set_autostart`)
- clock/timing helpers (`get_time`, `get_day_seconds`, `get_tick_count`, `sleep`)
- script engine scheduling behavior (`set_yield`)

Use cases:

- deterministic interval loops
- one-shot autorun scripts on startup

### 9) Firmware Interface (Advanced Lua)

Core capabilities:

- call firmware procedures (`call_event_proc`, `call_func_ptr`)
- logical event APIs (`post_levent_to_ui`, `post_levent_for_npt`, `get_levent_*`, `set_levent_*`)

Use cases:

- advanced model-specific automation
- deep integration when standard commands are not enough

### 10) Display, Console, and Overlays

Core capabilities:

- LCD/backlight/title-line controls (`set_backlight`, `set_lcd_display`, `set_draw_title_line`)
- script console controls (`print`, `cls`, `console_redraw`, `set_console_layout`, `print_screen`)
- drawing primitives in Lua (`draw_line`, `draw_rect`, `draw_string`, `draw.xxx`)
- text input helper (`textbox`, Lua)

Use cases:

- on-camera status overlays
- debugging script state visually

### 11) RAW and Raw-Buffer Workflows

Core capabilities:

- enable/disable RAW and noise-reduction behavior (`set_raw`, `set_raw_nr`, `get_raw_nr`, `get_raw_support`)
- raw merge/develop helpers (`raw_merge_start`, `raw_merge_add_file`, `raw_merge_end`, `set_raw_develop`)
- raw hook operations via `rawop.*` (Lua) for reading/modifying raw buffers before file save

Use cases:

- computational photography experiments
- custom raw-based analysis and post-processing pipelines

### 12) CHDK Config and System Behavior

Core capabilities:

- ALT mode control (`enter_alt`, `exit_alt`, `get_alt_mode`)
- CHDK config read/write (`get_config_value`, `set_config_value`)
- load/save CHDK config files (`load_config_file`, `save_config_file`, Lua)
- build/platform info (`get_buildinfo`, `get_platform_id`, `get_digic`)
- histogram controls (`get_histo_range`, `shot_histo_enable`)

Use cases:

- script-managed CHDK profile switching
- reproducible camera automation presets

### 13) Programming Helpers (Lua)

Core capabilities:

- bitwise ops (`bitand`, `bitor`, `bitxor`, shifts)
- direct memory access (`peek`, `poke`)
- integer math module `imath.*` (trig, log, rounding, conversions)

Use cases:

- fast in-camera calculations
- compact algorithmic scripts without external dependencies

### 14) Motion Detection

Core capabilities:

- motion trigger and cell-level metrics (`md_detect_motion`, `md_get_cell_diff`, `md_get_cell_val`)
- AF assist timing for MD testing (`md_af_on_time`)

Use cases:

- lightning and wildlife/event triggers
- low-latency trigger logic compared with host-side vision loops

### 15) USB/PTP Interface and Remote Sync

Core capabilities:

- USB remote state and timing (`get_usb_power`, `set_remote_timing`)
- USB message channel over PTP (`read_usb_msg`, `write_usb_msg`, helpers)
- mode switching over USB (`switch_mode_usb`)
- force USB/AV state for testing (`usb_force_active`, `force_analog_av`)
- shot synchronization (`usb_sync_wait`)
- USB capture helpers (`get_usb_capture_support`, `init_usb_capture`, capture timeout/target)

Use cases:

- host-controlled capture workflows
- multi-camera synchronization
- robust CHDKPTP-based remote shooting pipelines

### 16) Tone Curves (Lua)

Core capabilities:

- enable/disable and select tone curve files (`set_curve_state`, `set_curve_file`, getters)

Use cases:

- camera-side tonal style control in automated sessions

## Practical Workflows You Can Build Now

With these capabilities, typical production workflows include:

- intervalometer with exposure/focus lock
- sunrise/sunset bracketing and HDR sequences
- focus stacking scripts
- lightning/motion-trigger capture
- USB-synced multi-camera trigger
- host-assisted remote capture and transfer with CHDKPTP
- raw-hook based quality checks before storing files

## Compatibility and Safety Notes

- Not every function works on every camera/firmware build.
- Some commands are marked obsolete and replaced by newer variants.
- Lua generally exposes more advanced APIs than uBASIC.
- Validate scripts on your exact model before unattended operation.
- Prefer conservative timing/retry logic for USB/PTP workflows.

For exact per-function syntax, return values, and firmware nuances, always use:

- [CHDK Scripting Cross Reference Page](https://chdk.fandom.com/wiki/CHDK_Scripting_Cross_Reference_Page)

## Appendix: Full Function Inventory (Cross-Reference Snapshot)

This appendix mirrors the cross-reference categories and function names so you have a complete capability index in one local file.

### Lens Functions

`get_focus`, `get_focus_mode`, `get_focus_ok`, `get_focus_state`, `get_IS_mode`, `get_zoom`, `get_zoom_steps`, `get_sd_over_modes`, `set_mf`, `set_aflock`, `set_focus`, `set_focus_interlock_bypass`, `set_zoom`, `set_zoom_rel`, `set_zoom_speed`

### Depth of Field

`get_dofinfo`, `get_dof`, `get_far_limit`, `get_near_limit`, `get_focal_length`, `get_hyp_dist`

### Exposure Functions

`get_av`, `get_av96`, `get_bv96`, `get_ev`, `get_iso`, `get_iso_market`, `get_iso_mode`, `get_iso_real`, `get_max_av96`, `get_min_av96`, `get_nd_present`, `get_nd_value_ev96`, `get_nd_current_ev96`, `get_sv96`, `get_tv96`, `get_user_av_id`, `get_user_av96`, `get_user_tv_id`, `get_user_tv96`, `set_aelock`, `set_av`, `set_av_rel`, `set_av96`, `set_av96_direct`, `set_ev`, `set_iso`, `set_iso_mode`, `set_iso_real`, `set_nd_filter`, `set_sv96`, `set_tv`, `set_tv_rel`, `set_tv96`, `set_tv96_direct`, `set_user_av_by_id`, `set_user_av_by_id_rel`, `set_user_av96`, `set_user_tv_by_id`, `set_user_tv_by_id_rel`, `set_user_tv96`, `get_live_histo`, `get_imager_active`, `get_current_tv96`, `get_current_av96`

### APEX96 Conversion

`iso_to_sv96`, `sv96_to_iso`, `iso_real_to_market`, `iso_market_to_real`, `sv96_real_to_market`, `sv96_market_to_real`, `aperture_to_av96`, `av96_to_aperture`, `usec_to_tv96`, `tv96_to_usec`, `seconds_to_tv96`

### Camera Functions

`get_canon_image_format`, `get_canon_raw_support`, `get_capture_mode`, `get_display_mode`, `get_drive_mode`, `get_flash_mode`, `get_flash_params_count`, `get_flash_ready`, `get_meminfo`, `get_mode`, `get_movie_status`, `get_orientation_sensor`, `get_parameter_data`, `get_prop`, `get_prop_str`, `get_propset`, `get_quality`, `get_resolution`, `get_shooting`, `get_temperature`, `get_vbatt`, `get_video_button`, `get_video_recording`, `is_capture_mode_valid`, `play_sound`, `reboot`, `restore`, `set_canon_image_format`, `set_capture_mode`, `set_capture_mode_canon`, `set_led`, `set_movie_status`, `set_prop`, `set_prop_str`, `set_quality`, `set_record`, `set_resolution`, `set_clock`, `shut_down`

### Keypad and Switches

`click`, `is_key`, `is_pressed`, `press`, `release`, `shoot`, `wait_click`, `wheel_left`, `wheel_right`, `set_exit_key`

### SD Card Functions

`get_disk_size`, `get_exp_count`, `get_image_dir`, `file_browser`, `get_free_disk_space`, `get_jpg_count`, `get_partitionInfo`, `set_file_attributes`, `swap_partitions`

### Script Status Functions

`autostarted`, `end`, `get_autostart`, `get_day_seconds`, `get_tick_count`, `get_time`, `set_autostart`, `set_yield`, `sleep`

### Firmware Interface

`call_event_proc(name, ...)`, `call_func_ptr(fptr, ...)`, `get_levent_def`, `get_levent_def_by_index`, `get_levent_index`, `post_levent_for_npt`, `post_levent_to_ui`, `set_levent_active`, `set_levent_script_mode`

### Display and Text Console

`set_backlight`, `set_lcd_display`, `set_draw_title_line`, `get_draw_title_line`, `cls`, `console_redraw`, `print`, `print_screen`, `set_console_autoredraw`, `set_console_layout`

### LCD Graphics

`draw.xxx`, `draw_ellipse`, `draw_ellipse_filled`, `draw_line`, `draw_pixel`, `draw_rect`, `draw_rect_filled`, `draw_string`, `textbox`, `get_gui_screen_width`, `get_gui_screen_height`

### RAW

`get_raw`, `get_raw_count`, `get_raw_nr`, `get_raw_support`, `raw_merge_add_file`, `raw_merge_end`, `raw_merge_start`, `set_raw`, `set_raw_develop`, `set_raw_nr`, `rawop.*`

### CHDK Functionality

`enter_alt`, `exit_alt`, `get_alt_mode`, `get_buildinfo`, `get_digic`, `get_config_value`, `set_config_autosave`, `load_config_file`, `save_config_file`, `get_histo_range`, `get_platform_id`, `set_config_value`, `shot_histo_enable`

### Programming

`bitand(a, b)`, `bitnot(a)`, `bitor(a, b)`, `bitshl(a)`, `bitshri(a)`, `bitshru(a)`, `bitxor(a, b)`, `peek`, `poke`

### Motion Detection

`md_detect_motion`, `md_get_cell_diff`, `md_get_cell_val`, `md_af_on_time`

### USB Port Interface

`get_usb_power`, `set_remote_timing`, `read_usb_msg`, `write_usb_msg`, `usb_msg_table_to_string`, `switch_mode_usb`, `usb_force_active`, `force_analog_av`, `usb_sync_wait`, `get_usb_capture_support`, `init_usb_capture`, `get_usb_capture_target`, `set_usb_capture_timeout`

### Tone Curves

`get_curve_file`, `get_curve_state`, `set_curve_file`, `set_curve_state`

### imath Functions

`imath.scale`, `imath.pi2`, `imath.pi`, `imath.pi_2`, `imath.muldiv`, `imath.mul`, `imath.div`, `imath.rad`, `imath.deg`, `imath.sinr`, `imath.cosr`, `imath.tanr`, `imath.asinr`, `imath.acosr`, `imath.atanr`, `imath.polr`, `imath.recr`, `imath.sind`, `imath.cosd`, `imath.tand`, `imath.asind`, `imath.acosd`, `imath.atand`, `imath.pold`, `imath.recd`, `imath.pow`, `imath.log`, `imath.log2`, `imath.log10`, `imath.sqrt`, `imath.int`, `imath.frac`, `imath.ceil`, `imath.floor`, `imath.round`

