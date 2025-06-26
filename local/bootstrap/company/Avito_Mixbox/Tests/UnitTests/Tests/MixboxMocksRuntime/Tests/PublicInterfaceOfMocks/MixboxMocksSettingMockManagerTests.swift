import MixboxMocksRuntime
import MixboxTestsFoundation

final class MixboxMocksSettingMockManagerTests: BaseMixboxMocksRuntimeTests {
    let mock = MockMocksTestsFixtureProtocol()
    
    func test___RegisterMocksSetUpAction___sets_up_mock_manager() {
        parameterized_test___mock_manager_is_set_up_after {
            let setUpAction = RegisterMocksSetUpAction(
                testCase: self,
                mockRegisterer: dependencies.resolve()
            )
            
            _ = setUpAction.setUp()
        }
    }
    
    func test___setMockManager___sets_up_mock_manager() {
        parameterized_test___mock_manager_is_set_up_after {
            let factory = dependencies.resolve() as MockManagerFactory
            
            XCTAssert(factory is ConfiguredMockManagerFactory)
            
            mock.setMockManager(
                factory.mockManager()
            )
        }
    }
    func test___MockRegisterer___sets_up_mock_manager() {
        parameterized_test___mock_manager_is_set_up_after {
            let registerer = dependencies.resolve() as MockRegisterer
            
            XCTAssert(registerer is MockRegistererImpl)
            
            registerer.register(mock: mock)
        }
    }

    // TODO: Allow user to disambiguate expressions more easily.
    // This is not good: `(mock.verify().function() as VerificationFunctionBuilder<(), Int>).isCalled()`
    private func parameterized_test___mock_manager_is_set_up_after(_ setUpAction: () -> ()) {
        
        // Stubbing is supported for unconfigured mocks
        mock
            .stub()
            .function()
            .thenReturn(42)
        
        // Calling is supported for unconfigured mocks
        assertPasses {
            XCTAssertEqual(
                mock.function(),
                42
            )
        }
        
        // Verification is supported for unconfigured mocks
        assertPasses {
            (mock.verify().function() as VerificationFunctionBuilder<(), Int>).isCalled()
        }
        
        setUpAction()
        
        // Verification works as before
        assertPasses {
            (mock.verify().function() as VerificationFunctionBuilder<(), Int>)
                .isCalled(times: .exactly(1), timeout: 0)
        }
        
        // Calling works as before
        assertPasses {
            XCTAssertEqual(
                mock.function(),
                42
            )
        }
        
        // Old and new mock manager are synced. Both old an new calls are tracked
        assertPasses {
            (mock.verify().function() as VerificationFunctionBuilder<(), Int>)
                .isCalled(times: .exactly(2), timeout: 0)
        }
    }
}
