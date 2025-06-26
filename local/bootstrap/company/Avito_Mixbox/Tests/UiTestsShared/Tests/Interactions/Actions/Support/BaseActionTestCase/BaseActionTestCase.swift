import XCTest
import MixboxUiTestsFoundation
import TestsIpc

// TODO: Test fails.
// TODO: Test that LoggingElementInteractionWithDependenciesPerformer reports attachments in nestedFailures in InteractionFailure.
// TODO: Test touchesAreBlocked == true. Lost touches are a major problem at the moment.
// TODO: Test coordinates.
// TODO: Split. This class is too bloated.
class BaseActionTestCase: TestCase {
    
    // MARK: - Screen
    
    override func precondition() {
        super.precondition()
        
        open(screen: screen)
            .waitUntilViewIsLoaded()
    }
    
    var screen: ActionsTestsViewPageObject {
        return pageObjects.actionsTestsView.default
    }
}
