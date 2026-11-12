import CoreText
import Foundation
import UIKit

/// Uygulama (React Native) ile widget arasında App Group üzerinden paylaşılan ayarlar.
/// Uygulama tarafı `src/widgetBridge.ts` içinde ExtensionStorage ile yazar.
/// ExtensionStorage sayıları tam sayı (Int) olarak kaydeder.
enum SharedSettings {
    /// app.json'daki App Group ile aynı olmalı.
    static let appGroupID = "group.com.ramazan29arslan.pati"

    static var defaults: UserDefaults {
        UserDefaults(suiteName: appGroupID) ?? .standard
    }

    /// 1 = açık, 0 = kapalı. Hiç ayarlanmadıysa açık.
    static var reactToBattery: Bool {
        (defaults.object(forKey: "reactToBattery") as? NSNumber)?.boolValue ?? true
    }

    /// Uygulamanın en son kaydettiği pil yüzdesi (0-100).
    static var lastBatteryLevel: Float? {
        guard let percent = defaults.object(forKey: "batteryPercent") as? NSNumber else { return nil }
        return percent.floatValue / 100
    }

    /// Uygulamadan elle seçilen ruh hali ("awake", "sleepy"...). Yoksa otomatik.
    static var moodOverride: Mood? {
        (defaults.string(forKey: "moodOverride")).flatMap(Mood.init(rawValue:))
    }

    static var lastCharging: Bool {
        (defaults.object(forKey: "batteryCharging") as? NSNumber)?.boolValue ?? false
    }
}

enum BatteryReader {
    /// Önce cihazdan okur; okunamazsa uygulamanın kaydettiği değeri kullanır.
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
}

/// Paketteki tüm .ttf dosyalarını çalışma anında kaydeder.
/// Böylece yeni karakter eklerken Info.plist'e dokunmak gerekmez.
enum FontRegistry {
    private static let registration: Void = {
        let urls = (Bundle.main.urls(forResourcesWithExtension: "ttf", subdirectory: nil) ?? [])
            + (Bundle.main.urls(forResourcesWithExtension: "ttf", subdirectory: "assets") ?? [])
        for url in urls {
            CTFontManagerRegisterFontsForURL(url as CFURL, .process, nil)
        }
    }()

    static func registerAll() { _ = registration }
}
