# Title: Slide
# Authors: Juha Ylitalo, http://www.ylitalot.com
# Description: Shortcut for [![desc](img_t.jpg "desc")](img_l.jpg "desc")
#
# Syntax: {% slide img "desc" %}
#
# Output:
# <a href="img_l.jpg" title="desc"><img src="img_t.jpg" alt="desc" title="desc"></a>
#

module Jekyll

  class SlideTag < Liquid::Tag
    @slide = nil

    def initialize(tag_name, markup, tokens)
      attributes = ['image', 'title']

      if markup =~ /(?<image>\S.*\s+)(?:"|')(?<title>[^"']+)?(?:"|')?/i
        @slide = attributes.reduce({}) { |slide, attr| slide[attr] = $~[attr].strip if $~[attr]; slide }
      end
      super
    end

    def render(context)
      if @slide
        image = @slide["image"]
        title = @slide["title"]
        "<a href=\"#{image}_l.jpg\" title=\"#{title}\"><img src=\"#{image}_t.jpg\" alt=\"#{title}\" title=\"#{title}\" /></a>"
      else
        "Error processing input, expected syntax: {% slide /path/to/image \"title text\" %}"
      end
    end
  end
end

Liquid::Template.register_tag('slide', Jekyll::SlideTag)
