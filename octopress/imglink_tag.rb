# Title: Link with image as anchor
# Authors: Juha Ylitalo, http://www.ylitalot.com/
# Description: Short cut for [![desc](img.jpg "desc")](/link/)
#
# Syntax {% img_link img.jpg "desc" link %}
#
# Output:
# <a href="link" title="desc"><img src="img.jpg" alt="desc" title="desc"></a>
#

module Jekyll

  class ImageLinkTag < Liquid::Tag
    @image_link = nil

    def initialize(tag_name, markup, tokens)
      attributes = ['image', 'link', 'title']

      if markup =~ /(?<image>\S.*\s+)(?:"|')(?<title>[^"']+)(?:"|') (?<link>.*)?/i
        @image_link = attributes.reduce({}) { |image_link, attr| image_link[attr] = $~[attr].strip if $~[attr]; image_link }
      end
      super
    end

    def render(context)
      if @image_link
        image = @image_link["image"]
        title = @image_link["title"]
        link = @image_link["link"]
        "<a href=\"#{link}\" title=\"#{title}\"><img src=\"#{image}\" alt=\"#{title}\" title=\"#{title}\" /></a>"
      else
        "Error processing input, expected syntax: {% image_link /path/to/image \"title text\" link %}"
      end
    end
  end
end

Liquid::Template.register_tag('img_link', Jekyll::ImageLinkTag)
