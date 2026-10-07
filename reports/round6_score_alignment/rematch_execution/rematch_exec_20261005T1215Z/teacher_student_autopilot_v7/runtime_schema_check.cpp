#include "json-schema-to-grammar.h"
#include "llama-grammar.h"
#include <iostream>
#include <string>

// Use the exact deployed converter and parser without loading model weights.
int main() {
    try {
        const std::string text((std::istreambuf_iterator<char>(std::cin)),
            std::istreambuf_iterator<char>());
        const common_json input = common_json::parse(text);
        const std::string grammar_text = input.contains("grammar")
            ? input.at("grammar").get<std::string>()
            : json_schema_to_grammar(input.at("schema"), true);
        const std::string root = input.value("root", std::string("root"));
        common_json checks = common_json::array();
        bool all_match = true;
        for (const auto & example : input.at("examples")) {
            auto * grammar = llama_grammar_init_impl(nullptr, grammar_text.c_str(),
                root.c_str(), false, nullptr, 0, nullptr, 0);
            if (grammar == nullptr) {
                throw std::runtime_error("pinned grammar parser rejected generated rules");
            }
            bool accepted = false;
            try {
                llama_grammar_accept_str(*grammar, example.at("text").get<std::string>());
                for (const auto & stack : llama_grammar_get_stacks(grammar)) {
                    accepted = accepted || stack.empty();
                }
            } catch (const std::exception &) {
                accepted = false;
            }
            llama_grammar_free_impl(grammar);
            const bool expected = example.at("expected").get<bool>();
            all_match = all_match && accepted == expected;
            checks.push_back({{"accepted", accepted}, {"expected", expected}});
        }
        std::cout << common_json({{"all_examples_match_expectations", all_match},
            {"checks", checks}, {"grammar", grammar_text}}).dump() << '\n';
        return all_match ? 0 : 2;
    } catch (const std::exception & error) {
        std::cerr << error.what() << '\n';
        return 1;
    }
}
