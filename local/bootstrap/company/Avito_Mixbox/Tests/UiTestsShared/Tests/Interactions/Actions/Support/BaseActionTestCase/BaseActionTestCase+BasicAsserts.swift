import XCTest
import MixboxUiTestsFoundation
import MixboxIpc
import TestsIpc

extension BaseActionTestCase {
    func assertAndResetResult(
        equals expectedResult: ActionsTestsViewActionResult,
        describeFailure: (ActionsTestsViewActionResult, ActionsTestsViewActionResult) -> String)
    {
        let timeout: TimeInterval = 5
        let pollInterval: TimeInterval = 0.1
        
        waiter.wait(timeout: timeout, interval: pollInterval) { [synchronousIpcClient] in
            let actualResult = synchronousIpcClient.callOrFail(
                method: GetActionResultIpcMethod()
            )
            
            return actualResult == expectedResult
        }
        
        let actualResult = synchronousIpcClient.callOrFail(
            method: GetActionResultIpcMethod()
        )
        
        // Better to reset UI before failing

        resetUi()
        
        XCTAssertEqual(expectedResult, actualResult, describeFailure(expectedResult, actualResult))
    }
}
