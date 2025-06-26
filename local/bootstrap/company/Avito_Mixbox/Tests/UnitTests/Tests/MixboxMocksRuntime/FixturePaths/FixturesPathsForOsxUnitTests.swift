// Note: file is in OsxUnitTests target.
// It is used to debug code generation in Xcode.

import PathKit

final class FixturesPathsForOsxUnitTests {
    private init() {}
    
    static let folderPath = Path(#filePath) + "../../Fixtures"
    
    static func allFiles() throws -> [Path] {
        return try folderPath
            .recursiveChildren()
            .filter { $0.isFile }
    }
}
