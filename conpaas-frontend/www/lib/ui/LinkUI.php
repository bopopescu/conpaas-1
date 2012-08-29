<?php
/*
 * Copyright (c) 2010-2012, Contrail consortium.
 * All rights reserved.
 *
 * Redistribution and use in source and binary forms,
 * with or without modification, are permitted provided
 * that the following conditions are met:
 *
 *  1. Redistributions of source code must retain the
 *     above copyright notice, this list of conditions
 *     and the following disclaimer.
 *  2. Redistributions in binary form must reproduce
 *     the above copyright notice, this list of
 *     conditions and the following disclaimer in the
 *     documentation and/or other materials provided
 *     with the distribution.
 *  3. Neither the name of the Contrail consortium nor the
 *     names of its contributors may be used to endorse
 *     or promote products derived from this software
 *     without specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND
 * CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES,
 * INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
 * DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
 * CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
 * SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
 * BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
 * SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
 * INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
 * WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
 * (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT
 * OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
 * POSSIBILITY OF SUCH DAMAGE.
 */

function LinkUI($text, $href) {
	return new LinkUI($text, $href);
}

class LinkUI {

	const POS_RIGHT = 'right';
	const POS_LEFT = 'left';

	private $text;
	private $href;
	private $external = false;
	private $class = 'link';
	private $iconURL = 'images/link_s.png';
	private $iconPosition = self::POS_RIGHT;

	public function __construct($text, $href) {
		$this->text = $text;
		$this->href = $href;
	}

	public function setIconPosition($position) {
		if ($position !== self::POS_LEFT && $position !== self::POS_RIGHT) {
			return $this;
		}
		$this->iconPosition = $position;
		return $this;
	}

	public function setExternal($external) {
		$this->external = $external;
		return $this;
	}

	public function setIconURL($url) {
		$this->iconURL = $url;
		return $this;
	}

	public function addClass($class) {
		$this->class .= ' '.$class;
		return $this;
	}

	private function renderSymbol() {
		return
			'<img src="'.$this->iconURL.'" style="vertical-align: middle;" />';
	}

	public function __toString() {
		$target = $this->external ? 'target="new"' : '';
		$leftSymbol = '';
		$rightSymbol = '';
		if ($this->iconPosition == self::POS_LEFT) {
			$leftSymbol = $this->renderSymbol();
		} else {
			$rightSymbol = $this->renderSymbol();
		}
		return
		'<div class="'.$this->class.'">'
			.$leftSymbol
			.'<a href="'.$this->href.'" '.$target.'>'.$this->text.'</a>'
			.$rightSymbol
		.'</div>';
	}
}