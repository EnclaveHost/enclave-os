// Resource limits, not reduced web functionality. Apps start on demand.
user_pref("dom.ipc.processCount", 2);
user_pref("dom.ipc.processPrelaunch.enabled", false);
user_pref("browser.tabs.unloadOnLowMemory", true);
user_pref("browser.sessionhistory.max_total_viewers", 0);
user_pref("browser.sessionstore.interval", 60000);
user_pref("browser.cache.disk.capacity", 65536);
user_pref("browser.startup.homepage", "about:blank");
user_pref("browser.newtabpage.enabled", false);
user_pref("network.prefetch-next", false);
user_pref("network.dns.disablePrefetch", true);
user_pref("network.predictor.enabled", false);
user_pref("datareporting.healthreport.uploadEnabled", false);
user_pref("toolkit.telemetry.enabled", false);
user_pref("toolkit.telemetry.unified", false);
user_pref("layout.frame_rate", 30);
user_pref("fission.autostart", true);
user_pref("javascript.options.content_process_write_protect_code", true);
// Keep accessibility, media, animations, certificate checks and Safe Browsing.
