import kegg_pull.link_to_dict_cli as ltd_cli
import dev.utils as u


def test_main_help(mocker):
    u.assert_main_help(mocker=mocker, module=ltd_cli, subcommand='link-to-dict')
