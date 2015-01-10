
images = []
f = File.open("todo.txt")
f.each_line do |line|
  if line.include?("source/images/") and line.include?("_l.jpg")
    image_file = line.strip.split(" source")[1].sub("_l.jpg","")
    # puts "### found image: >#{image_file}<"
    images += [image_file]
  end # if
end # f.each_line
f.close

puts "### #{images.length} images found from todo list"

markdowns = 0
references = 0
need_work = 0

Dir.glob("source/_posts/*markdown").each do |fname|
  markdowns += 1
  f = File.open(fname)
  f.each_line do |line|
    images.each do |img|
      if line.include?(img)
        references += 1
        if not line.start_with?("{% gslide ") and not line.include?("_c.jpg") and not line.start_with?("{% image_link ")
          puts "#{fname.split("/")[-1]}: #{line}"
          need_work += 1
        end # if
      end # if
    end # images.each
  end # f.each_line
  f.close
end # Dir.glob.each
puts "### #{markdowns} markdown files found."
puts "### #{references} references to images."

if need_work > 0
  puts "### #{need_work} images must be loaded into G+"
else
  flist = ""
  images.each do |fname|
    flist += " source#{fname}_l.jpg"
  end # images.each
  # cmdline = "git filter-branch --index-filter 'git rm --cached --ignore-unmatch #{flist}' HEAD"
  cmdline = "git filter-branch --index-filter 'git rm --cached --ignore-unmatch #{flist}' -- --all"
  puts "### #{cmdline}"
  system(cmdline)
  system("git for-each-ref --format=\"%(refname)\" refs/original/ | xargs -n 1 git update-ref -d")
  system("git reflog expire --expire=now --all")
end # if>