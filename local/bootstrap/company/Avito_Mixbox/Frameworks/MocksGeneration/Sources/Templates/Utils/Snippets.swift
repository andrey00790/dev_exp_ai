import SourceryRuntime

// Resulable pieces of code
public final class Snippets {
    private init() {
    }
    
    // Current implementation probaly contains a lot of errors. TODO: Read Swift grammar, write test.
    public static func stringLiteral(_ string: String?) -> String {
        return string.map(default: "nil") { string in
            if string.contains("\n") {
                return """
                \"\"\"
                \(string.replacingOccurrences(of: "\"\"\"", with: "\\\"\\\"\\\""))
                \"\"\"
                """
            } else {
                return """
                "\(string.replacingOccurrences(of: "\"", with: "\\\""))"
                """
            }
        }
    }
    
    // MARK: - Specific for current templates
    
    public static func tupledArgumentsType(methodParameters: [MethodParameter]) -> String {
        return methodParameters.render(
            separator: ", ",
            surround: { "(\($0))" },
            transform: { _, parameter in
                parameter.typeName.validTypeNameReplacingImplicitlyUnrappedOptionalWithPlainOptional
            }
        )
    }
    
    public static func argumentName(index: Int) -> String {
        return "argument\(index)"
    }
    
    public static func matcherArgumentName(index: Int) -> String {
        return "matcher\(index)"
    }
    
    public static func variableNameStringLiteral(variable: Variable) -> String {
        return identifier(
            value: "\(variable.name)"
        )
    }
    
    public static func functionIdentifier(method: Method) -> String {
        return identifier(
            value: "func/\(method.name)"
        )
    }
    
    // Multiline literal is necessary, because value can be multiline.
    // TODO: Add escaping!
    public static func identifier(value: String) -> String {
        """
        \"\"\"
        \(value)
        \"\"\"
        """
    }
    
    // MARK: - Escaping closures
    
    public static func withoutActuallyEscaping(
        closureName: String,
        closureTypeName: TypeName,
        isThrowingOrRethrowing: Bool,
        returnType: String,
        body: String)
        -> String
    {
        let tryCode = isThrowingOrRethrowing ? "try " : ""
        
        return """
        \(tryCode)withoutActuallyEscaping(\(closureName), do: { (\(closureName): @escaping \(closureTypeName.validTypeNameReplacingImplicitlyUnrappedOptionalWithPlainOptional)) -> \(returnType) in
            \(body.indent())
        })
        """
    }

    // Note: we can't be sure that parameter is actually a closure,
    // for example, if type is typealias and this typealias can't be resolved.
    public static func withoutActuallyEscaping(
        parameters: [MethodParameter],
        argumentName: (_ index: Int) -> String,
        isThrowingOrRethrowing: Bool,
        returnType: String,
        body: String)
        -> String
    {
        parameters.enumerated().reduce(body) { (body, pair) -> String in
            if pair.element.isNonEscapingClosure {
                return withoutActuallyEscaping(
                    closureName: argumentName(pair.offset),
                    closureTypeName: pair.element.typeName,
                    isThrowingOrRethrowing: isThrowingOrRethrowing,
                    returnType: returnType,
                    body: body
                )
            } else {
                return body
            }
        }
    }
    
    // MARK: - Generic for Swift
    
    /// Returns just name of argument if label is same as name.
    /// Returns labeled argument otherwise.
    ///
    /// Imagine this function:
    ///
    /// `func x(a b: Int)`
    ///
    /// `a` is label, `b` is name.
    ///
    /// `labeledArgument(label: "a", name: "b")` will return `"a b"`
    /// `labeledArgument(label: "x", name: "x")` will return just `"x"`
    ///
    public static func labeledArgumentForFunctionSignature(label: String?, name: String) -> String {
        return labeledArgumentForFunctionSignatureWhileValuesArentEmpty(
            label: label.convertEmptyToNil(),
            name: name.convertEmptyToNil()
        )
    }
    
    private static func labeledArgumentForFunctionSignatureWhileValuesArentEmpty(label: String?, name: String?) -> String {
        switch (label, name) {
        case (nil, nil):
            return "_"
        case let (nil, name?):
            return "_ \(name)"
        case let (label?, nil):
            // That's not a valid case in Swift. TODO: Assertion failure?
            return "\(label) _"
        case let (label?, name?):
            if label == name {
                return name
            } else {
                return "\(label) \(name)"
            }
        }
    }
}
