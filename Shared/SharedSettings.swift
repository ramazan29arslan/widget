import CoreText
import Foundation
import UIKit

/// Uygulama ile widget arasında App Group üzerinden paylaşılan ayarlar.
enum SharedSettings {
    /// project.yml içindeki APP_GROUP ile aynı olmalı.
    static let appGroupID = "group.com.ramazan29arslan.pati"

    static var defaults: UserDefaults {
        UserDefaults(suiteName: appGroupID) ?? .standard
    }

    static var reactToBattery: Bool {
        get { defaults.object(forKey: "reactToBattery") as? Bool ?? true }
        set { defaults.set(newValue, forKey: "reactToBattery") }
    }

    /// Uygulama açıkken kaydedilen son pil bilgisi (widget okuyamazsa yedek).
    static var lastBatteryLevel: Float? {
        get { defaults.object(forKey: "lastBatteryLevel") as? Float }
        set { defaults.set(newValue, forKey: "lastBatteryLevel") }
    }

    static var lastCharging: Bool {
        get { defaults.bool(forKey: "lastCharging") }
        set { defaults.set(newValue, forKey: "lastCharging") }
    }
}

enum BatteryReader {
    @MainActor
    static func read() -> (level: Float?, charging: Bool) {
        let device = UIDevice.current
        device.isBatteryMonitoringEnabled = true
        let level = device.batteryLevel
        if level >= 0 {
            let charging = device.batteryState == .charging || device.batteryState == .full
            return (level, charging)
        }
        return (SharedSettings.lastBatteryLevel, SharedSettings.lastCharging)
    }

    @MainActor
    static func saveCurrent() {
        let reading = read()
        if let level = reading.level { SharedSettings.lastBatteryLevel = level }
        SharedSettings.lastCharging = reading.charging
    }
}

/// Paketteki tüm .ttf dosyalarını çalışma anında kaydeder.
/// Böylece yeni karakter eklerken Info.plist'e dokunmak gerekmez.
enum FontRegistry {
    private static let registration: Void = {
        let urls = Bundle.main.urls(forResourcesWithExtension: "ttf", subdirectory: nil) ?? []
        for url in urls {
            CTFontManagerRegisterFontsForURL(url as CFURL, .process, nil)
        }
    }()

    static func registerAll() { _ = registration }
}
